from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

CONTACTS_TEXT = (
    "<b>Автосервис «AutoPro»</b>\n\n"
    "📍 <b>Адрес:</b> Calle de la Motor, 42\n"
    "   03001 Alicante, España\n\n"
    "📞 <b>Телефон:</b> +34 966 123 456\n\n"
    "🕐 <b>Часы работы:</b>\n"
    "   Пн–Пт: 09:00 – 18:00\n"
    "   Сб: 09:00 – 14:00\n"
    "   Вс: выходной\n\n"
    "📧 <b>Email:</b> info@autopro.es"
)


@router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀ Назад", callback_data="back_to_menu")]
        ]
    )
    await callback.message.edit_text(CONTACTS_TEXT, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
