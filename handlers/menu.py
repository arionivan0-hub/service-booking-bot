from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from database.crud import get_user_by_telegram_id
from handlers.keyboards import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    user = await get_user_by_telegram_id(message.from_user.id)

    if user is None:
        await state.set_state("RegistrationState:name")
        await message.answer(
            f"Добро пожаловать, {message.from_user.first_name}!\n\n"
            "Я бот для записи на услуги автосервиса.\n"
            "Для начала давайте познакомимся.\n\n"
            "Введите ваше имя:"
        )
        return

    await message.answer(
        f"С возвращением, {user.name}!\n\n"
        "Чем могу помочь?",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "<b>Доступные команды:</b>\n\n"
        "/start - Главное меню\n"
        "/help - Помощь\n"
        "/cancel - Отменить текущее действие\n\n"
        "Или используйте кнопки меню:"
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.", reply_markup=get_main_menu_keyboard())
        return

    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=get_main_menu_keyboard(),
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()
