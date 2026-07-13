from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.crud import get_active_appointments_by_user, cancel_appointment
from services.time_slots import format_date_display

router = Router()


@router.callback_query(F.data == "my_appointments")
async def show_my_appointments(callback: CallbackQuery) -> None:
    telegram_id = callback.from_user.id
    appointments = await get_active_appointments_by_user(telegram_id)

    if not appointments:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="◀ Назад", callback_data="back_to_menu")]
            ]
        )
        await callback.message.edit_text(
            "У вас нет активных записей.",
            reply_markup=keyboard,
        )
        await callback.answer()
        return

    buttons = []
    text_parts = ["<b>Ваши записи:</b>\n"]

    for appt in appointments:
        display_date = format_date_display(appt.date)
        svc = appt.service
        text_parts.append(
            f"• {svc.name} — {display_date} в {appt.time_slot}\n"
            f"  Стоимость: {int(svc.price)} ₽"
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"❌ Отменить: {svc.name} {display_date}",
                    callback_data=f"cancel_appt:{appt.id}",
                )
            ]
        )

    buttons.append(
        [InlineKeyboardButton(text="◀ Назад", callback_data="back_to_menu")]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("\n".join(text_parts), reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_appt:"))
async def cancel_my_appointment(callback: CallbackQuery) -> None:
    appt_id = int(callback.data.split(":")[1])
    success = await cancel_appointment(appt_id)

    if success:
        await callback.message.edit_text("✅ Запись отменена.")
    else:
        await callback.message.edit_text("Не удалось отменить запись.")

    await callback.answer()
