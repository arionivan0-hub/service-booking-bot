import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

import config
from database.crud import get_all_services
from database.engine import async_session
from database.models import User, Appointment, Service
from sqlalchemy import select, func
from handlers.keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router()


def _is_admin(telegram_id: int) -> bool:
    if not config.ADMIN_IDS:
        return False
    return telegram_id in config.ADMIN_IDS


class AdminAddServiceState(StatesGroup):
    name = State()
    price = State()
    duration = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer("Нет доступа.")
        return

    text = (
        "<b>Админ-панель</b>\n\n"
        "/stats - Статистика\n"
        "/services - Список услуг\n"
        "/add_service - Добавить услугу\n"
        "/audit - Последние действия\n"
        "/active - Активные записи"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return

    async with async_session() as session:
        users_count = (await session.execute(select(func.count(User.id)))).scalar()
        services_count = (await session.execute(select(func.count(Service.id)))).scalar()
        active_appts = (await session.execute(
            select(func.count(Appointment.id)).where(Appointment.status == "active")
        )).scalar()
        total_appts = (await session.execute(select(func.count(Appointment.id)))).scalar()

    text = (
        "<b>Статистика</b>\n\n"
        f"Пользователей: {users_count}\n"
        f"Услуг: {services_count}\n"
        f"Активных записей: {active_appts}\n"
        f"Всего записей: {total_appts}"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("services"))
async def cmd_services(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return

    services = await get_all_services()
    if not services:
        await message.answer("Услуг нет.")
        return

    lines = ["<b>Услуги:</b>\n"]
    for s in services:
        lines.append(f"  ID={s.id} | {s.name} | {int(s.price)} \u20bd | {s.duration} мин")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("active"))
async def cmd_active(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return

    async with async_session() as session:
        result = await session.execute(
            select(Appointment)
            .join(User, Appointment.user_id == User.id)
            .join(Service, Appointment.service_id == Service.id)
            .where(Appointment.status == "active")
            .order_by(Appointment.date, Appointment.time_slot)
            .limit(20)
        )
        appointments = list(result.scalars().all())

    if not appointments:
        await message.answer("Активных записей нет.")
        return

    lines = ["<b>Активные записи:</b>\n"]
    for a in appointments:
        lines.append(f"  {a.date} {a.time_slot} | user_id={a.user_id} | service_id={a.service_id}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("add_service"))
async def cmd_add_service(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    await state.set_state(AdminAddServiceState.name)
    await message.answer("Введите название услуги:")


@router.message(AdminAddServiceState.name)
async def process_service_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminAddServiceState.price)
    await message.answer("Введите стоимость (число, руб.):")


@router.message(AdminAddServiceState.price)
async def process_service_price(message: Message, state: FSMContext) -> None:
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer("Введите корректное число:")
        return

    await state.update_data(price=price)
    await state.set_state(AdminAddServiceState.duration)
    await message.answer("Введите длительность (минут):")


@router.message(AdminAddServiceState.duration)
async def process_service_duration(message: Message, state: FSMContext) -> None:
    try:
        duration = int(message.text.strip())
    except ValueError:
        await message.answer("Введите целое число:")
        return

    data = await state.get_data()

    async with async_session() as session:
        svc = Service(name=data["name"], price=data["price"], duration=duration)
        session.add(svc)
        await session.commit()
        await session.refresh(svc)

    await state.clear()
    await message.answer(
        f"Услуга добавлена: {svc.name} ({int(svc.price)} \u20bd, {svc.duration} мин)\nID: {svc.id}",
        reply_markup=get_main_menu_keyboard(),
    )

    from services.audit import log_action
    await log_action(message.from_user.id, "service_added", f"name={svc.name}, id={svc.id}")


@router.message(Command("audit"))
async def cmd_audit(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return

    from services.audit import get_audit_log
    logs = await get_audit_log(limit=10)

    if not logs:
        await message.answer("Журнал пуст.")
        return

    lines = ["<b>Последние действия:</b>\n"]
    for entry in logs:
        ts = entry["created_at"].strftime("%d.%m %H:%M") if entry["created_at"] else "?"
        lines.append(f"  [{ts}] {entry['telegram_id']} | {entry['action']}")
        if entry["details"]:
            lines.append(f"    {entry['details']}")
    await message.answer("\n".join(lines), parse_mode="HTML")
