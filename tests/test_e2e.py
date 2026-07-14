import asyncio
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, User as AiogramUser, Chat, Update


def _make_message(text: str, user_id: int = 123456789, chat_id: int = 123456789) -> Message:
    return Message(
        message_id=1,
        date=1700000000,
        text=text,
        chat=Chat(id=chat_id, type="private"),
        from_user=AiogramUser(id=user_id, is_bot=False, first_name="Test"),
    )


def _make_callback(data: str, user_id: int = 123456789) -> CallbackQuery:
    msg = _make_message("placeholder", user_id=user_id)
    return CallbackQuery(
        id="test_callback",
        chat_instance="test",
        from_user=AiogramUser(id=user_id, is_bot=False, first_name="Test"),
        message=msg,
        data=data,
    )


@pytest.mark.asyncio
async def test_start_new_user():
    from handlers.menu import cmd_start

    msg = _make_message("/start")
    state = FSMContext(storage=MemoryStorage(), key=("bot", msg.chat.id, msg.from_user.id))

    with patch("handlers.menu.get_user_by_telegram_id", new_callable=AsyncMock, return_value=None):
        await cmd_start(msg, state)

    current = await state.get_state()
    assert current is not None


@pytest.mark.asyncio
async def test_start_registered_user():
    from handlers.menu import cmd_start

    msg = _make_message("/start")
    state = FSMContext(storage=MemoryStorage(), key=("bot", msg.chat.id, msg.from_user.id))

    mock_user = MagicMock()
    mock_user.name = "Test User"

    with patch("handlers.menu.get_user_by_telegram_id", new_callable=AsyncMock, return_value=mock_user):
        mock_answer = AsyncMock()
        msg.answer = mock_answer
        await cmd_start(msg, state)

    mock_answer.assert_called_once()
    assert "Test User" in mock_answer.call_args[0][0]


@pytest.mark.asyncio
async def test_registration_name_valid():
    from handlers.registration import process_name

    msg = _make_message("Иван")
    state = FSMContext(storage=MemoryStorage(), key=("bot", msg.chat.id, msg.from_user.id))
    await state.set_state("RegistrationState:name")

    mock_answer = AsyncMock()
    msg.answer = mock_answer
    await process_name(msg, state)

    current = await state.get_state()
    assert "phone" in current.lower()
    data = await state.get_data()
    assert data["name"] == "Иван"


@pytest.mark.asyncio
async def test_registration_name_invalid():
    from handlers.registration import process_name

    msg = _make_message("А")
    state = FSMContext(storage=MemoryStorage(), key=("bot", msg.chat.id, msg.from_user.id))
    await state.set_state("RegistrationState:name")

    mock_answer = AsyncMock()
    msg.answer = mock_answer
    await process_name(msg, state)

    current = await state.get_state()
    assert "name" in current.lower()


@pytest.mark.asyncio
async def test_registration_phone_invalid():
    from handlers.registration import process_phone

    msg = _make_message("abc")
    state = FSMContext(storage=MemoryStorage(), key=("bot", msg.chat.id, msg.from_user.id))
    await state.set_state("RegistrationState.phone")
    await state.update_data(name="Test")

    mock_answer = AsyncMock()
    msg.answer = mock_answer
    await process_phone(msg, state)

    current = await state.get_state()
    assert "phone" in current.lower()


@pytest.mark.asyncio
async def test_help_command():
    from handlers.menu import cmd_help

    msg = _make_message("/help")
    mock_answer = AsyncMock()
    msg.answer = mock_answer
    await cmd_help(msg)

    mock_answer.assert_called_once()
    assert "/start" in mock_answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_not_authorized():
    from handlers.admin import cmd_admin

    msg = _make_message("/admin", user_id=999999)
    mock_answer = AsyncMock()
    msg.answer = mock_answer
    await cmd_admin(msg)

    mock_answer.assert_called_once()
    assert "Нет доступа" in mock_answer.call_args[0][0]
