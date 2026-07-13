from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from database.crud import get_user_by_telegram_id

router = Router()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🔧 Выбрать услугу", callback_data="choose_service")],
        [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_appointments")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = await get_user_by_telegram_id(message.from_user.id)

    if user is None:
        text = (
            f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
            "Я бот для записи на услуги автосервиса.\n"
            "Для начала выберите услугу из меню below."
        )
    else:
        text = (
            f"👋 С возвращением, {user.name}!\n\n"
            "Чем могу помочь?"
        )

    await message.answer(text, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()
