import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.asyncio
async def test_create_and_read_user(session, seed_db):
    from database.models import User

    user = User(telegram_id=99999, name="Integration User", phone="+79009999999")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert user.id is not None
    assert user.telegram_id == 99999
    assert user.name == "Integration User"


@pytest.mark.asyncio
async def test_create_appointment(session, seed_db):
    from database.models import Appointment

    appt = Appointment(
        user_id=1,
        service_id=1,
        date="2026-07-20",
        time_slot="10:00",
        status="active",
    )
    session.add(appt)
    await session.commit()
    await session.refresh(appt)

    assert appt.id is not None
    assert appt.status == "active"
    assert appt.created_at is not None


@pytest.mark.asyncio
async def test_unique_constraint(session, seed_db):
    from database.models import Appointment
    from sqlalchemy.exc import IntegrityError

    appt1 = Appointment(user_id=1, service_id=1, date="2026-07-21", time_slot="10:00", status="active")
    session.add(appt1)
    await session.commit()

    appt2 = Appointment(user_id=1, service_id=1, date="2026-07-21", time_slot="10:00", status="active")
    session.add(appt2)

    with pytest.raises(IntegrityError):
        await session.commit()

    await session.rollback()


@pytest.mark.asyncio
async def test_cancel_appointment(session, seed_db):
    from database.models import Appointment

    appt = Appointment(user_id=1, service_id=1, date="2026-07-22", time_slot="11:00", status="active")
    session.add(appt)
    await session.commit()
    await session.refresh(appt)

    appt.status = "cancelled"
    await session.commit()
    await session.refresh(appt)

    assert appt.status == "cancelled"


@pytest.mark.asyncio
async def test_unique_allows_different_status(session, seed_db):
    from database.models import Appointment

    appt1 = Appointment(user_id=1, service_id=1, date="2026-07-23", time_slot="10:00", status="active")
    session.add(appt1)
    await session.commit()

    appt2 = Appointment(user_id=1, service_id=1, date="2026-07-23", time_slot="10:00", status="cancelled")
    session.add(appt2)
    await session.commit()
    await session.refresh(appt2)

    assert appt2.id is not None
