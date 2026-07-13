from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.crud import get_all_services
from handlers.booking import BookingState

router = Router()


@router.callback_query(F.data == "choose_service")
async def show_services(callback: CallbackQuery) -> None:
    services = await get_all_services()

    buttons = []
    for svc in services:
        text = f"{svc.name}  —  {int(svc.price)} ₽, {svc.duration} мин"
        buttons.append(
            [InlineKeyboardButton(text=text, callback_data=f"svc:{svc.id}")]
        )
    buttons.append([InlineKeyboardButton(text="◀ Назад", callback_data="back_to_menu")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text("Выберите услугу:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("svc:"))
async def select_service(callback: CallbackQuery, state: FSMContext) -> None:
    service_id = int(callback.data.split(":")[1])
    await state.update_data(service_id=service_id)
    await state.set_state(BookingState.choose_date)

    from handlers.booking import show_dates
    await show_dates(callback, state)
