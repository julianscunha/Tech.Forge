"""
Catalog Favorite Service — Fase 11 Slice 4.5

CRUD operations for personal catalog favorites.
Mesmo padrão de app/services/catalog_source.py (Slice 4).
"""

from typing import Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog_favorite import CatalogFavorite


class CatalogFavoriteService:
    """Manage personal catalog favorites."""

    @staticmethod
    async def add(db: AsyncSession, module_id: str) -> CatalogFavorite:
        """Add a module to favorites (idempotent — return existing if already favorited)."""
        # Check if already exists
        result = await db.execute(
            select(CatalogFavorite).where(CatalogFavorite.module_id == module_id)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            return existing

        # Create new favorite
        favorite = CatalogFavorite(module_id=module_id)
        db.add(favorite)
        await db.commit()
        await db.refresh(favorite)
        return favorite

    @staticmethod
    async def list_ids(db: AsyncSession) -> Set[str]:
        """List all favorited module IDs as a set (efficient for membership checks)."""
        result = await db.execute(select(CatalogFavorite.module_id))
        return set(result.scalars().all())

    @staticmethod
    async def remove(db: AsyncSession, module_id: str) -> bool:
        """Remove a module from favorites. Return False if not existed."""
        result = await db.execute(
            select(CatalogFavorite).where(CatalogFavorite.module_id == module_id)
        )
        favorite = result.scalar_one_or_none()

        if favorite is None:
            return False

        await db.delete(favorite)
        await db.commit()
        return True
