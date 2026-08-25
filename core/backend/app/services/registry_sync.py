"""Sync do registry in-memory → tabela modules do DB (Fase 4 §21 Dashboard).

Raiz do bug: o Loader popula só o registry in-memory; count_installed()
conta a tabela DB, que ninguém escrevia. Um upsert resolve.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import registry

logger = logging.getLogger("techforge.registry_sync")


async def sync_registry_to_db(db: AsyncSession) -> None:
    """Upsert de cada entrada do registry in-memory para a tabela modules."""
    from app.models.registry import Module
    from app.services.registry import CategoryService, ModuleService

    categories = {c.name: c for c in await CategoryService.get_all(db)}

    for entry in registry.all():
        if entry.status in (ModuleStatus.INVALID, ModuleStatus.INCOMPATIBLE):
            continue
        category = categories.get(entry.category)
        existing = await ModuleService.get_by_module_id(db, entry.module_id)
        enabled = entry.status != ModuleStatus.DISABLED
        if existing:
            existing.version = entry.version
            existing.description = entry.description
            existing.is_enabled = enabled
            existing.category_id = category.id if category else existing.category_id
        else:
            db.add(Module(
                module_id=entry.module_id,
                name=entry.name,
                version=entry.version,
                description=entry.description,
                vendor=entry.vendor,
                author=entry.author,
                platform_min_version=entry.platform_min_version,
                platform_max_version=entry.platform_max_version,
                is_enabled=enabled,
                category_id=category.id if category else None,
            ))
    await db.commit()
    logger.info("Registry synced to DB (%d modules).", len(registry.all()))


async def sync_from_request(app=None) -> None:
    """Helper para rotas: abre sessão e sincroniza."""
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await sync_registry_to_db(db)
