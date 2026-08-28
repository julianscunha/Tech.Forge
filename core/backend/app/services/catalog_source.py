"""
Catalog Source Service — Fase 11 Slice 4 §18/§19

CRUD for catalog source configuration. Invalidates cache on mutations.
Mesmo padrão de app/services/publisher.py (Fase 10).
"""

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog_source import CatalogSourceConfig
from app.package_manager.catalog_source import CatalogSource


class CatalogSourceService:
    """CRUD operations for catalog sources."""

    @staticmethod
    async def add(
        db: AsyncSession,
        name: str,
        url: str,
        source_type: CatalogSource,
        enabled: bool = True,
    ) -> CatalogSourceConfig:
        """Add a new catalog source."""
        source_id = str(uuid.uuid4())[:8]
        source = CatalogSourceConfig(
            id=source_id,
            name=name,
            url=url,
            type=source_type.value,
            enabled=enabled,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        return source

    @staticmethod
    async def list_all(db: AsyncSession) -> Sequence[CatalogSourceConfig]:
        """List all catalog sources, ordered by creation date."""
        result = await db.execute(
            select(CatalogSourceConfig).order_by(CatalogSourceConfig.created_at)
        )
        return result.scalars().all()

    @staticmethod
    async def remove(
        db: AsyncSession,
        source_id: str,
        cache=None,
    ) -> bool:
        """Remove a catalog source by id and invalidate its cache."""
        result = await db.execute(
            select(CatalogSourceConfig).where(CatalogSourceConfig.id == source_id)
        )
        source = result.scalar_one_or_none()

        if source is None:
            return False

        await db.delete(source)
        await db.commit()

        # Invalidate cache if provided
        if cache is not None:
            cache.invalidate(source_id)

        return True

    @staticmethod
    async def toggle(
        db: AsyncSession,
        source_id: str,
        enabled: bool,
    ) -> Optional[CatalogSourceConfig]:
        """Toggle a source's enabled status."""
        result = await db.execute(
            select(CatalogSourceConfig).where(CatalogSourceConfig.id == source_id)
        )
        source = result.scalar_one_or_none()

        if source is None:
            return None

        source.enabled = enabled
        await db.commit()
        await db.refresh(source)
        return source

    @staticmethod
    async def update_url(
        db: AsyncSession,
        source_id: str,
        new_url: str,
        cache=None,
    ) -> Optional[CatalogSourceConfig]:
        """Update a source's URL and invalidate its cache."""
        result = await db.execute(
            select(CatalogSourceConfig).where(CatalogSourceConfig.id == source_id)
        )
        source = result.scalar_one_or_none()

        if source is None:
            return None

        source.url = new_url
        await db.commit()
        await db.refresh(source)

        # Invalidate cache if provided
        if cache is not None:
            cache.invalidate(source_id)

        return source
