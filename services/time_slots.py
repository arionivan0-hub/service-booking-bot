from datetime import datetime, timedelta, timezone
import logging

import config
from database.crud import get_booked_slots

logger = logging.getLogger(__name__)

MSK = timezone(timedelta(hours=config.TZ_OFFSET))


def _get_work_end(d) -> int:
    if d.weekday() == 5:
        return config.SAT_WORK_END
    return config.WORK_END


async def get_free_slots(date_str: str, service_id: int, duration_minutes: int = 60) -> list[str]:
    booked = await get_booked_slots(date_str, service_id)
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    work_end = _get_work_end(d)

    duration_slots = max(-(-duration_minutes // 60), 1)

    all_slots = []
    for hour in range(config.WORK_START, work_end):
        slot = f"{hour:02d}:00"
        all_slots.append(slot)

    booked_hours = set()
    for slot in booked:
        h = int(slot.split(":")[0])
        for offset in range(duration_slots):
            booked_hours.add(h + offset)

    return [s for s in all_slots if int(s.split(":")[0]) not in booked_hours]


def get_available_dates(count: int | None = None) -> list[str]:
    if count is None:
        count = config.BOOKING_AHEAD_DAYS
    today = datetime.now(MSK).date()
    dates = []
    while len(dates) < count:
        today += timedelta(days=1)
        if config.SUNDAY_CLOSED and today.weekday() == 6:
            continue
        dates.append(today.strftime("%Y-%m-%d"))
    return dates


def format_date_display(date_str: str) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    wd = weekdays[d.weekday()]
    return f"{d.strftime('%d.%m')} ({wd})"
