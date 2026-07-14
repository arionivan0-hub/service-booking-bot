import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.asyncio
async def test_start_new_user():
    from handlers.menu import cmd_start
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage

    msg = AsyncMock()
    msg.from_user.id = 123456789
    msg.from_user.first_name = "Test"
    msg.chat.id = 123456789

    state = FSMContext(storage=MemoryStorage(), key=("bot", msg.chat.id, msg.from_user.id))

    with patch("handlers.menu.get_user_by_telegram_id", new_callable=AsyncMock, return_value=None):
        await cmd_start(msg, state)

    msg.answer.assert_called_once()
    current = await state.get_state()
    assert current is not None


@pytest.mark.asyncio
async def test_start_registered_user():
    from handlers.menu import cmd_start
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage

    msg = AsyncMock()
    msg.from_user.id = 123456789
    msg.chat.id = 123456789

    state = FSMContext(storage=MemoryStorage(), key=("bot", msg.chat.id, msg.from_user.id))

    mock_user = MagicMock()
    mock_user.name = "Test User"

    with patch("handlers.menu.get_user_by_telegram_id", new_callable=AsyncMock, return_value=mock_user):
        await cmd_start(msg, state)

    msg.answer.assert_called_once()
    assert "Test User" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_registration_name_valid():
    from handlers.registration import process_name
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage

    msg = AsyncMock()
    msg.text = "Иван"
    msg.from_user.id = 123456789
    msg.chat.id = 123456789

    state = FSMContext(storage=MemoryStorage(), key=("bot", msg.chat.id, msg.from_user.id))
    await state.set_state("RegistrationState:name")

    await process_name(msg, state)

    current = await state.get_state()
    assert "phone" in current.lower()
    data = await state.get_data()
    assert data["name"] == "Иван"


@pytest.mark.asyncio
async def test_registration_name_invalid():
    from handlers.registration import process_name
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage

    msg = AsyncMock()
    msg.text = "А"
    msg.from_user.id = 123456789
    msg.chat.id = 123456789

    state = FSMContext(storage=MemoryStorage(), key=("bot", msg.chat.id, msg.from_user.id))
    await state.set_state("RegistrationState:name")

    await process_name(msg, state)

    current = await state.get_state()
    assert "name" in current.lower()


@pytest.mark.asyncio
async def test_registration_phone_invalid():
    from handlers.registration import process_phone
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage

    msg = AsyncMock()
    msg.text = "abc"
    msg.from_user.id = 123456789
    msg.chat.id = 123456789

    state = FSMContext(storage=MemoryStorage(), key=("bot", msg.chat.id, msg.from_user.id))
    await state.set_state("RegistrationState.phone")
    await state.update_data(name="Test")

    await process_phone(msg, state)

    current = await state.get_state()
    assert "phone" in current.lower()


@pytest.mark.asyncio
async def test_help_command():
    from handlers.menu import cmd_help

    msg = AsyncMock()
    await cmd_help(msg)

    msg.answer.assert_called_once()
    assert "/start" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_admin_not_authorized():
    from handlers.admin import cmd_admin

    msg = AsyncMock()
    msg.from_user.id = 999999

    await cmd_admin(msg)

    msg.answer.assert_called_once()
    assert "Нет доступа" in msg.answer.call_args[0][0]
