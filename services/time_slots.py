from datetime import datetime, timedelta

from database.crud import get_booked_slots

WORK_START = 9
WORK_END = 18
STEP_HOURS = 1


async def get_free_slots(date_str: str, service_id: int) -> list[str]:
    booked = await get_booked_slots(date_str, service_id)

    all_slots = []
    for hour in range(WORK_START, WORK_END, STEP_HOURS):
        slot = f"{hour:02d}:00"
        all_slots.append(slot)

    return [s for s in all_slots if s not in booked]


def get_available_dates(count: int = 7) -> list[str]:
    today = datetime.now().date()
    dates = []
    for i in range(1, count + 1):
        d = today + timedelta(days=i)
        dates.append(d.strftime("%Y-%m-%d"))
    return dates


def format_date_display(date_str: str) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    wd = weekdays[d.weekday()]
    return f"{d.strftime('%d.%m')} ({wd})"
