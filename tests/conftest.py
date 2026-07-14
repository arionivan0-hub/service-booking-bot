import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from database.engine import Base
from database.models import User, Service, Appointment


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as sess:
        yield sess
        await sess.rollback()


@pytest.fixture
async def seed_db(session):
    services = [
        Service(name="Test Oil Change", price=1500.0, duration=30),
        Service(name="Test Diagnostics", price=3000.0, duration=60),
        Service(name="Test Brake Pads", price=4000.0, duration=90),
    ]
    session.add_all(services)
    await session.commit()

    user = User(telegram_id=123456789, name="Test User", phone="+79001234567")
    session.add(user)
    await session.commit()
