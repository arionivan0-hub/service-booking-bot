from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .engine import async_session
from .models import User, Service, Appointment


async def get_or_create_user(
    telegram_id: int,
    name: str,
    phone: str,
) -> User:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(telegram_id=telegram_id, name=name, phone=phone)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            user.name = name
            user.phone = phone
            await session.commit()

        return user


async def get_user_by_telegram_id(telegram_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def get_all_services() -> list[Service]:
    async with async_session() as session:
        result = await session.execute(select(Service))
        return list(result.scalars().all())


async def get_service_by_id(service_id: int) -> Service | None:
    async with async_session() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id)
        )
        return result.scalar_one_or_none()


async def create_appointment(
    user_id: int,
    service_id: int,
    date: str,
    time_slot: str,
) -> Appointment:
    async with async_session() as session:
        appointment = Appointment(
            user_id=user_id,
            service_id=service_id,
            date=date,
            time_slot=time_slot,
            status="active",
        )
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment)
        return appointment


async def get_active_appointments_by_user(telegram_id: int) -> list[Appointment]:
    async with async_session() as session:
        result = await session.execute(
            select(Appointment)
            .options(selectinload(Appointment.service))
            .join(User, Appointment.user_id == User.id)
            .where(User.telegram_id == telegram_id)
            .where(Appointment.status == "active")
            .order_by(Appointment.date, Appointment.time_slot)
        )
        return list(result.scalars().all())


async def cancel_appointment(appointment_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appointment = result.scalar_one_or_none()

        if appointment is None:
            return False

        appointment.status = "cancelled"
        await session.commit()
        return True


async def get_booked_slots(date: str, service_id: int) -> list[str]:
    async with async_session() as session:
        result = await session.execute(
            select(Appointment.time_slot)
            .where(Appointment.date == date)
            .where(Appointment.service_id == service_id)
            .where(Appointment.status == "active")
        )
        return list(result.scalars().all())


async def seed_services():
    async with async_session() as session:
        result = await session.execute(select(Service))
        if result.scalars().first() is not None:
            return

        default_services = [
            Service(name="Замена масла", price=1500.0, duration=30),
            Service(name="Диагностика двигателя", price=3000.0, duration=60),
            Service(name="Замена тормозных колодок", price=4000.0, duration=90),
            Service(name="Шиномонтаж (4 шт.)", price=2500.0, duration=45),
            Service(name="Комплексная мойка", price=800.0, duration=20),
        ]
        session.add_all(default_services)
        await session.commit()
