import re

from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.crud import get_or_create_user, get_user_by_telegram_id, update_user_profile
from handlers.keyboards import get_main_menu_keyboard

router = Router()

PHONE_RE = re.compile(r"^[\d\+\-\(\) ]{7,15}$")


class RegistrationState(StatesGroup):
    name = State()
    phone = State()
    edit_name = State()
    edit_phone = State()


def _skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="reg_skip")]
        ]
    )


def _is_valid_name(text: str) -> bool:
    if text.startswith("/"):
        return False
    if len(text.strip()) < 2:
        return False
    return bool(re.search(r"[a-zA-Zа-яА-ЯёЁ]", text))


def _is_valid_phone(text: str) -> bool:
    if text.startswith("/"):
        return False
    return bool(PHONE_RE.match(text.strip()))


@router.message(RegistrationState.name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not _is_valid_name(name):
        await message.answer(
            "Введите корректное имя (минимум 2 буквы, без команд):"
        )
        return

    await state.update_data(name=name)
    await state.set_state(RegistrationState.phone)
    await message.answer(
        f"Приятно познакомиться, {name}!\n"
        "Теперь введите ваш номер телефона:",
        reply_markup=_skip_keyboard(),
    )


@router.callback_query(F.data == "reg_skip", RegistrationState.phone)
async def skip_phone(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    telegram_id = callback.from_user.id

    user = await get_or_create_user(
        telegram_id=telegram_id,
        name=data["name"],
        phone="не указан",
    )

    await state.clear()
    await callback.message.edit_text(
        f"Регистрация завершена!\n\n"
        f"Имя: {user.name}\n"
        f"Телефон: {user.phone}\n\n"
        "Теперь вы можете записываться на услуги.",
    )
    await callback.answer()
    await callback.message.answer("Главное меню:", reply_markup=get_main_menu_keyboard())


@router.message(RegistrationState.phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if not _is_valid_phone(phone):
        await message.answer(
            "Введите корректный номер телефона (7-15 цифр, допускаются +, -, пробелы):"
        )
        return

    data = await state.get_data()
    telegram_id = message.from_user.id

    user = await get_or_create_user(
        telegram_id=telegram_id,
        name=data["name"],
        phone=phone,
    )

    await state.clear()
    await message.answer(
        f"Регистрация завершена!\n\n"
        f"Имя: {user.name}\n"
        f"Телефон: {user.phone}\n\n"
        "Теперь вы можете записываться на услуги.",
    )
    await message.answer("Главное меню:", reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "edit_profile")
async def edit_profile(callback: CallbackQuery, state: FSMContext) -> None:
    user = await get_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Сначала зарегистрируйтесь: /start")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить имя", callback_data="edit_name")],
            [InlineKeyboardButton(text="Изменить телефон", callback_data="edit_phone")],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_menu")],
        ]
    )
    await callback.message.edit_text(
        f"Ваш профиль:\n\n"
        f"Имя: {user.name}\n"
        f"Телефон: {user.phone}\n\n"
        f"Что хотите изменить?",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "edit_name")
async def start_edit_name(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RegistrationState.edit_name)
    await callback.message.edit_text("Введите новое имя:")
    await callback.answer()


@router.message(RegistrationState.edit_name)
async def process_edit_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not _is_valid_name(name):
        await message.answer("Введите корректное имя (минимум 2 букв, без команд):")
        return

    telegram_id = message.from_user.id
    await update_user_profile(telegram_id, name=name)
    await state.clear()
    await message.answer(f"Имя обновлено: {name}", reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "edit_phone")
async def start_edit_phone(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RegistrationState.edit_phone)
    await callback.message.edit_text(
        "Введите новый номер телефона:",
        reply_markup=_skip_keyboard(),
    )
    await callback.answer()


@router.message(RegistrationState.edit_phone)
async def process_edit_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if not _is_valid_phone(phone):
        await message.answer("Введите корректный номер телефона (7-15 цифр):")
        return

    telegram_id = message.from_user.id
    await update_user_profile(telegram_id, phone=phone)
    await state.clear()
    await message.answer(f"Телефон обновлён: {phone}", reply_markup=get_main_menu_keyboard())
