import logging
from datetime import datetime, timedelta

from aiogram import Bot

import config
from services.time_slots import MSK

logger = logging.getLogger(__name__)

_bot_ref: Bot | None = None


def set_bot(bot: Bot):
    global _bot_ref
    _bot_ref = bot


def _parse_reminder_time(time_str: str) -> datetime | None:
    try:
        date_part, time_part = time_str.split(" ")
        return datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M").replace(tzinfo=MSK)
    except (ValueError, AttributeError):
        return None


async def schedule_reminders(bot: Bot, appointment_id: int, date_str: str, time_str: str, user_telegram_id: int):
    appt_time = _parse_reminder_time(f"{date_str} {time_str}")
    if appt_time is None:
        return

    now = datetime.now(MSK)
    from services.scheduler import get_scheduler, start_scheduler
    scheduler = get_scheduler() or start_scheduler()

    for hours_before in config.REMINDER_HOURS:
        remind_at = appt_time - timedelta(hours=hours_before)
        if remind_at <= now:
            continue

        job_id = f"reminder_{appointment_id}_{hours_before}"

        async def send_reminder(uid=user_telegram_id, hrs=hours_before):
            try:
                await bot.send_message(
                    uid,
                    f"Напоминание: через {hrs} ч. у вас запись в автосервис.\n"
                    f"Подробнее: /start -> Мои записи",
                )
            except Exception as e:
                logger.warning("Failed to send reminder to %d: %s", uid, e)

        try:
            scheduler.add_job(
                send_reminder,
                "date",
                run_date=remind_at,
                id=job_id,
                replace_existing=True,
            )
            logger.info("Scheduled reminder for appointment %d at %s", appointment_id, remind_at)
        except Exception as e:
            logger.warning("Failed to schedule reminder: %s", e)


def cancel_reminders(appointment_id: int):
    from services.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler is None:
        return
    try:
        for hours_before in config.REMINDER_HOURS:
            job_id = f"reminder_{appointment_id}_{hours_before}"
            try:
                scheduler.remove_job(job_id)
            except Exception:
                pass
    except Exception:
        pass
