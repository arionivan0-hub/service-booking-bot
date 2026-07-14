import logging
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.engine import Base, async_session

logger = logging.getLogger(__name__)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


async def log_action(telegram_id: int, action: str, details: str | None = None):
    try:
        async with async_session() as session:
            entry = AuditLog(telegram_id=telegram_id, action=action, details=details)
            session.add(entry)
            await session.commit()
    except Exception as e:
        logger.warning("Audit log write failed: %s", e)


async def get_audit_log(limit: int = 50) -> list[dict]:
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        rows = result.scalars().all()
        return [
            {
                "telegram_id": r.telegram_id,
                "action": r.action,
                "details": r.details,
                "created_at": r.created_at,
            }
            for r in rows
        ]
