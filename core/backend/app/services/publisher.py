"""
Publisher Registry — CRUD (Fase 10 §10/§13)
================================================
"""
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.publisher import Publisher
from app.schemas.publisher import PublisherCreate


class PublisherService:

    @staticmethod
    async def get_all(db: AsyncSession) -> Sequence[Publisher]:
        result = await db.execute(select(Publisher).order_by(Publisher.id))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, publisher_id: str) -> Optional[Publisher]:
        result = await db.execute(select(Publisher).where(Publisher.id == publisher_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def register(db: AsyncSession, payload: PublisherCreate) -> Publisher:
        """Idempotente: se o id já existir, atualiza os campos em vez de duplicar."""
        existing = await PublisherService.get_by_id(db, payload.id)
        if existing is not None:
            for key, value in payload.model_dump().items():
                setattr(existing, key, value)
            await db.commit()
            await db.refresh(existing)
            return existing

        publisher = Publisher(**payload.model_dump())
        db.add(publisher)
        await db.commit()
        await db.refresh(publisher)
        return publisher

    @staticmethod
    async def set_trust_status(db: AsyncSession, publisher_id: str,
                               trust_status: str) -> Optional[Publisher]:
        publisher = await PublisherService.get_by_id(db, publisher_id)
        if publisher is None:
            return None
        publisher.trust_status = trust_status
        await db.commit()
        await db.refresh(publisher)
        return publisher

    @staticmethod
    async def revoke(db: AsyncSession, publisher_id: str) -> Optional[Publisher]:
        from app.module_trust.publisher import PublisherTrustStatus
        return await PublisherService.set_trust_status(
            db, publisher_id, PublisherTrustStatus.REVOKED.value)
