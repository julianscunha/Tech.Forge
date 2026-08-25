from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notifications import Notification

VALID_LEVELS = ("info", "warning", "error", "success")


class NotificationService:
    """Simple Core notification store (Fase 2, spec §10)."""

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        level: str,
        title: str,
        message: Optional[str] = None,
        module_id: Optional[str] = None,
    ) -> Notification:
        notification = Notification(
            level=level, title=title, message=message, module_id=module_id,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        unread_only: bool = False,
        limit: int = 100,
    ) -> Sequence[Notification]:
        stmt = select(Notification).order_by(Notification.created_at.desc()).limit(limit)
        if unread_only:
            stmt = stmt.where(Notification.read.is_(False))
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def count_unread(db: AsyncSession) -> int:
        result = await db.execute(
            select(func.count()).select_from(Notification).where(Notification.read.is_(False))
        )
        return int(result.scalar_one())

    @staticmethod
    async def mark_read(db: AsyncSession, notification_id: int) -> bool:
        result = await db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(read=True)
        )
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def mark_all_read(db: AsyncSession) -> int:
        result = await db.execute(
            update(Notification).where(Notification.read.is_(False)).values(read=True)
        )
        await db.commit()
        return result.rowcount
