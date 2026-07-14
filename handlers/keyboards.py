from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Выбрать услугу", callback_data="choose_service")],
        [InlineKeyboardButton(text="Мои записи", callback_data="my_appointments")],
        [InlineKeyboardButton(text="Мой профиль", callback_data="edit_profile")],
        [InlineKeyboardButton(text="Контакты", callback_data="contacts")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data=callback_data)]]
    )
