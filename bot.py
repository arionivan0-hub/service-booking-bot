import asyncio
import logging
import logging.handlers
import sys

from aiogram import Bot, Dispatcher

import config
from database import init_db
from database.crud import seed_services
from handlers import register_handlers
from middleware import AuthMiddleware, RateLimitMiddleware


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)

    file_handler = logging.handlers.RotatingFileHandler(
        "bot.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    bot = Bot(token=config.BOT_TOKEN)

    try:
        from aiogram.fsm.storage.redis import RedisStorage
        from redis.asyncio import Redis
        redis = Redis.from_url(config.REDIS_URL, decode_responses=True)
        storage = RedisStorage(redis=redis)
        logger.info("Using RedisStorage for FSM")
    except Exception as e:
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()
        logger.warning("Redis unavailable (%s), using MemoryStorage", e)

    dp = Dispatcher(storage=storage)

    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(RateLimitMiddleware(limit=0.5))
    dp.callback_query.middleware(AuthMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware(limit=0.3))

    register_handlers(dp)

    logger.info("Initializing database...")
    await init_db()
    from database.migrate import migrate
    await migrate()
    await seed_services()
    logger.info("Database ready.")

    from services.notifications import set_bot
    set_bot(bot)

    try:
        from services.scheduler import start_scheduler, shutdown_scheduler
        start_scheduler()
        scheduler_started = True
    except ImportError:
        logger.warning("APScheduler not available, reminders disabled")
        scheduler_started = False

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        if scheduler_started:
            from services.scheduler import shutdown_scheduler
            shutdown_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
