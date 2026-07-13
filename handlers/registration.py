from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.crud import get_or_create_user, get_user_by_telegram_id

router = Router()


class RegistrationState(StatesGroup):
    name = State()
    phone = State()


def _skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="reg_skip")]
        ]
    )


async def start_registration(message: Message, state: FSMContext) -> None:
    await state.set_state(RegistrationState.name)
    await message.answer(
        "Для записи на услуги нам cần знать ваше имя.\n"
        "Введите ваше имя:"
    )


@router.message(RegistrationState.name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Имя слишком короткое. Попробуйте ещё раз:")
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
        f"✅ Регистрация завершена!\n\n"
        f"Имя: {user.name}\n"
        f"Телефон: {user.phone}\n\n"
        "Теперь вы можете записываться на услуги.",
    )
    await callback.answer()

    from handlers.menu import get_main_menu_keyboard
    await callback.message.answer("Главное меню:", reply_markup=get_main_menu_keyboard())


@router.message(RegistrationState.phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    data = await state.get_data()
    telegram_id = message.from_user.id

    user = await get_or_create_user(
        telegram_id=telegram_id,
        name=data["name"],
        phone=phone,
    )

    await state.clear()
    await message.answer(
        f"✅ Регистрация завершена!\n\n"
        f"Имя: {user.name}\n"
        f"Телефон: {user.phone}\n\n"
        "Теперь вы можете записываться на услуги.",
    )

    from handlers.menu import get_main_menu_keyboard
    await message.answer("Главное меню:", reply_markup=get_main_menu_keyboard())


async def is_registered(telegram_id: int) -> bool:
    user = await get_user_by_telegram_id(telegram_id)
    return user is not None
