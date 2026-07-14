import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.crud import (
    get_active_appointments_by_user,
    cancel_appointment,
    get_user_by_telegram_id,
)
from services.time_slots import format_date_display
from handlers.keyboards import get_main_menu_keyboard
from handlers.booking import BookingState, show_dates

logger = logging.getLogger(__name__)

router = Router()

PAGE_SIZE = 5


def _build_appointments_page(appointments, page: int):
    total = len(appointments)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = appointments[start:end]

    buttons = []
    text_parts = [f"<b>Ваши записи:</b> (стр. {page + 1}/{total_pages})\n"]

    for appt in page_items:
        display_date = format_date_display(appt.date)
        svc = appt.service
        text_parts.append(
            f"  {svc.name} - {display_date} в {appt.time_slot}\n"
            f"  Стоимость: {int(svc.price)} \u20bd"
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"Перенести: {svc.name[:15]} {display_date}",
                    callback_data=f"reschedule:{appt.id}",
                )
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"Отменить: {svc.name[:15]} {display_date}",
                    callback_data=f"cancel_appt:{appt.id}:{appt.user_id}",
                )
            ]
        )

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="< Назад", callback_data=f"appt_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Далее >", callback_data=f"appt_page:{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="В меню", callback_data="back_to_menu")])

    return "\n".join(text_parts), InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "my_appointments")
async def show_my_appointments(callback: CallbackQuery) -> None:
    telegram_id = callback.from_user.id
    appointments = await get_active_appointments_by_user(telegram_id)

    if not appointments:
        await callback.message.edit_text(
            "У вас нет активных записей.",
            reply_markup=get_main_menu_keyboard(),
        )
        await callback.answer()
        return

    text, keyboard = _build_appointments_page(appointments, 0)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("appt_page:"))
async def paginate_appointments(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id
    appointments = await get_active_appointments_by_user(telegram_id)

    if not appointments:
        await callback.message.edit_text(
            "У вас нет активных записей.",
            reply_markup=get_main_menu_keyboard(),
        )
        await callback.answer()
        return

    text, keyboard = _build_appointments_page(appointments, page)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_appt:"))
async def cancel_my_appointment(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    appt_id = int(parts[1])
    owner_user_id = int(parts[2])

    user = await get_user_by_telegram_id(callback.from_user.id)
    if user is None or user.id != owner_user_id:
        await callback.answer("Нет прав для отмены", show_alert=True)
        return

    success = await cancel_appointment(appt_id, user_id=owner_user_id)

    if success:
        from services.notifications import cancel_reminders
        from services.audit import log_action
        cancel_reminders(appt_id)
        await log_action(callback.from_user.id, "appointment_cancelled", f"appointment_id={appt_id}")
        await callback.message.edit_text(
            "Запись отменена.",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await callback.message.edit_text(
            "Не удалось отменить запись.",
            reply_markup=get_main_menu_keyboard(),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("reschedule:"))
async def reschedule_appointment(callback: CallbackQuery, state: FSMContext) -> None:
    appt_id = int(callback.data.split(":")[1])

    from database.crud import get_appointment_with_user
    appt = await get_appointment_with_user(appt_id)

    if appt is None or appt.user.telegram_id != callback.from_user.id:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    await cancel_appointment(appt_id, user_id=appt.user_id)

    from services.notifications import cancel_reminders
    from services.audit import log_action
    cancel_reminders(appt_id)
    await log_action(callback.from_user.id, "appointment_rescheduled", f"appointment_id={appt_id}")

    await state.update_data(service_id=appt.service_id, reschedule_from=appt_id)
    await state.set_state(BookingState.choose_date)

    from handlers.keyboards import get_back_keyboard
    await callback.message.edit_text(
        f"Выберите новую дату для услуги: {appt.service.name}",
        reply_markup=get_back_keyboard("my_appointments"),
    )
    await callback.answer()

    from handlers.booking import show_dates
    await show_dates(callback, state)
