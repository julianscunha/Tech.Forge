from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.registry import Category, Module
from app.schemas.registry import CategoryCreate, ModuleCreate


class CategoryService:
    """CRUD operations for module categories."""

    @staticmethod
    async def get_all(db: AsyncSession) -> Sequence[Category]:
        result = await db.execute(select(Category).order_by(Category.name))
        return result.scalars().all()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Category | None:
        result = await db.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, payload: CategoryCreate) -> Category:
        category = Category(**payload.model_dump())
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def count(db: AsyncSession) -> int:
        result = await db.execute(select(func.count()).select_from(Category))
        return result.scalar_one()


class ModuleService:
    """
    CRUD operations for the module registry.
    This service will be extended by the Plugin Loader in Phase 2
    to handle lifecycle hooks (install, enable, disable, upgrade, uninstall).
    """

    @staticmethod
    async def get_all(db: AsyncSession) -> Sequence[Module]:
        result = await db.execute(
            select(Module)
            .options(selectinload(Module.category))
            .order_by(Module.name)
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_module_id(db: AsyncSession, module_id: str) -> Module | None:
        result = await db.execute(
            select(Module)
            .options(selectinload(Module.category))
            .where(Module.module_id == module_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, payload: ModuleCreate) -> Module:
        module = Module(**payload.model_dump())
        db.add(module)
        await db.commit()
        await db.refresh(module)
        return module

    @staticmethod
    async def count_installed(db: AsyncSession) -> int:
        result = await db.execute(select(func.count()).select_from(Module))
        return result.scalar_one()

    @staticmethod
    async def count_enabled(db: AsyncSession) -> int:
        result = await db.execute(
            select(func.count()).select_from(Module).where(Module.is_enabled.is_(True))
        )
        return result.scalar_one()
