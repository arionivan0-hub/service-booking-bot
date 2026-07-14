import logging
from sqlalchemy import text
from .engine import engine

logger = logging.getLogger(__name__)


async def migrate():
    async with engine.begin() as conn:
        try:
            await conn.execute(text(
                "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP NULL"
            ))
            await conn.execute(text(
                "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP NULL"
            ))
            logger.info("Migration: added cancelled_at and completed_at columns")
        except Exception as e:
            logger.warning("Migration skip (columns may already exist): %s", e)
