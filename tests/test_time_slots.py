import sys
import os
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.time_slots import (
    get_available_dates,
    format_date_display,
    _get_work_end,
)


def test_format_date_display():
    result = format_date_display("2026-07-14")
    assert "14.07" in result
    assert "Вт" in result


def test_format_date_display_weekend():
    result = format_date_display("2026-07-19")
    assert "19.07" in result
    assert "Вс" in result


def test_get_work_end_weekday():
    d = datetime(2026, 7, 15).date()  # Wednesday
    assert _get_work_end(d) == 18


def test_get_work_end_saturday():
    d = datetime(2026, 7, 18).date()  # Saturday
    assert _get_work_end(d) == 14


def test_get_available_dates_count():
    dates = get_available_dates(7)
    assert len(dates) == 7


def test_get_available_dates_no_sundays():
    dates = get_available_dates(14)
    for d in dates:
        dt = datetime.strptime(d, "%Y-%m-%d")
        assert dt.weekday() != 6, f"Sunday found: {d}"


def test_get_available_dates_format():
    dates = get_available_dates(3)
    for d in dates:
        datetime.strptime(d, "%Y-%m-%d")


@pytest.mark.asyncio
async def test_get_free_slots_no_bookings():
    with patch("services.time_slots.get_booked_slots", new_callable=AsyncMock, return_value=[]):
        from services.time_slots import get_free_slots
        slots = await get_free_slots("2026-07-15", 1, duration_minutes=60)
        assert len(slots) == 9
        assert "09:00" in slots
        assert "17:00" in slots


@pytest.mark.asyncio
async def test_get_free_slots_with_booking():
    with patch("services.time_slots.get_booked_slots", new_callable=AsyncMock, return_value=["10:00"]):
        from services.time_slots import get_free_slots
        slots = await get_free_slots("2026-07-15", 1, duration_minutes=60)
        assert "10:00" not in slots
        assert "09:00" in slots
        assert "11:00" in slots


@pytest.mark.asyncio
async def test_get_free_slots_90min_blocks_two():
    with patch("services.time_slots.get_booked_slots", new_callable=AsyncMock, return_value=["10:00"]):
        from services.time_slots import get_free_slots
        slots = await get_free_slots("2026-07-15", 1, duration_minutes=90)
        assert "10:00" not in slots
        assert "11:00" not in slots
        assert "09:00" in slots
        assert "12:00" in slots


@pytest.mark.asyncio
async def test_get_free_slots_saturday_shorter():
    with patch("services.time_slots.get_booked_slots", new_callable=AsyncMock, return_value=[]):
        from services.time_slots import get_free_slots
        slots = await get_free_slots("2026-07-18", 1, duration_minutes=60)
        assert "14:00" not in slots
        assert "13:00" in slots
