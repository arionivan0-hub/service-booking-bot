import logging

from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.crud import (
    get_service_by_id,
    get_user_by_telegram_id,
    create_appointment,
)
from services.time_slots import get_free_slots, get_available_dates, format_date_display
from handlers.keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router()


class BookingState(StatesGroup):
    choose_service = State()
    choose_date = State()
    choose_time = State()
    confirm = State()
    reschedule_pick_date = State()
    reschedule_pick_time = State()


async def show_dates(callback: CallbackQuery, state: FSMContext) -> None:
    dates = get_available_dates()

    buttons = []
    for d in dates:
        display = format_date_display(d)
        buttons.append(
            [InlineKeyboardButton(text=display, callback_data=f"date:{d}")]
        )
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="choose_service")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Выберите дату:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("date:"))
async def select_date(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        date_str = callback.data.split(":", 1)[1]
        await state.update_data(date=date_str)
        await state.set_state(BookingState.choose_time)

        data = await state.get_data()
        service_id = data["service_id"]

        service = await get_service_by_id(service_id)
        duration = service.duration if service else 60
        free_slots = await get_free_slots(date_str, service_id, duration_minutes=duration)

        if not free_slots:
            await callback.answer("На эту дату нет свободных слотов", show_alert=True)
            await state.set_state(BookingState.choose_date)
            return

        buttons = []
        for slot in free_slots:
            buttons.append(
                [InlineKeyboardButton(text=slot, callback_data=f"time:{slot}")]
            )
        buttons.append([InlineKeyboardButton(text="Назад к датам", callback_data="back_to_dates")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        display_date = format_date_display(date_str)
        await callback.message.edit_text(
            f"Свободные слоты на {display_date}:", reply_markup=keyboard
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Error in select_date")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("time:"))
async def select_time(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        time_slot = callback.data.split(":", 1)[1]
        await state.update_data(time_slot=time_slot)
        await state.set_state(BookingState.confirm)

        data = await state.get_data()

        if "service_id" not in data or "date" not in data:
            await state.clear()
            await callback.message.edit_text("Сессия истекла. Начните заново.", reply_markup=get_main_menu_keyboard())
            await callback.answer()
            return

        service = await get_service_by_id(data["service_id"])
        display_date = format_date_display(data["date"])

        summary = (
            f"<b>Подтвердите запись:</b>\n\n"
            f"Услуга: {service.name}\n"
            f"Стоимость: {int(service.price)} \u20bd\n"
            f"Длительность: {service.duration} мин\n\n"
            f"Дата: {display_date}\n"
            f"Время: {time_slot}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Подтвердить", callback_data="confirm_booking"),
                    InlineKeyboardButton(text="Отмена", callback_data="cancel_booking"),
                ]
            ]
        )

        await callback.message.edit_text(summary, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    except Exception as e:
        logger.exception("Error in select_time")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "confirm_booking")
async def confirm_booking(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        data = await state.get_data()

        if "service_id" not in data or "date" not in data or "time_slot" not in data:
            await state.clear()
            await callback.message.edit_text("Сессия истекла. Начните заново: /start")
            await callback.answer()
            return

        telegram_id = callback.from_user.id

        user = await get_user_by_telegram_id(telegram_id)
        if user is None:
            await callback.message.edit_text("Сначала зарегистрируйтесь: /start")
            await state.clear()
            await callback.answer()
            return

        service = await get_service_by_id(data["service_id"])
        if service is None:
            await callback.message.edit_text("Услуга не найдена. Начните заново: /start")
            await state.clear()
            await callback.answer()
            return

        try:
            appointment = await create_appointment(
                user_id=user.id,
                service_id=data["service_id"],
                date=data["date"],
                time_slot=data["time_slot"],
            )
        except ValueError:
            await callback.answer("Этот слот уже занят. Выберите другое время.", show_alert=True)
            await state.set_state(BookingState.choose_date)
            await show_dates(callback, state)
            return

        display_date = format_date_display(data["date"])
        await callback.message.edit_text(
            f"<b>Запись создана!</b>\n\n"
            f"{service.name} - {display_date} в {data['time_slot']}\n"
            f"Стоимость: {int(service.price)} \u20bd\n\n"
            f"Ждём вас! Если нужно отменить - используйте \"Мои записи\".",
            parse_mode="HTML",
        )
        await state.clear()
        await callback.answer()

        from services.audit import log_action
        await log_action(
            telegram_id,
            "booking_created",
            f"service={service.name}, date={data['date']}, time={data['time_slot']}",
        )

        from services.notifications import schedule_reminders
        await schedule_reminders(
            callback.bot, appointment.id,
            data["date"], data["time_slot"],
            telegram_id,
        )
    except Exception as e:
        logger.exception("Error in confirm_booking")
        await callback.answer("Произошла ошибка при записи", show_alert=True)


@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Запись отменена.",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_dates")
async def back_to_dates(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if "service_id" not in data:
        await state.clear()
        await callback.message.edit_text("Сессия истекла. Начните заново.", reply_markup=get_main_menu_keyboard())
        await callback.answer()
        return
    await state.set_state(BookingState.choose_date)
    await show_dates(callback, state)
