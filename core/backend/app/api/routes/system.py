"""/api/v1/system — Fase 12 §24 (Persistence health) / §30 (Migrations status).
"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.storage import storage_provider

router = APIRouter(prefix="/system", tags=["system"])


class StorageStatus(BaseModel):
    database: bool
    writable: bool


@router.get("/storage/status", response_model=StorageStatus, summary="Persistence health (Fase 12)")
async def get_storage_status(db: AsyncSession = Depends(get_db)) -> StorageStatus:
    health = await storage_provider.health_check(db)
    return StorageStatus(database=health.database, writable=health.writable)


class MigrationsStatus(BaseModel):
    head: Optional[str]
    current: Optional[str]
    up_to_date: bool


@router.get("/migrations/status", response_model=MigrationsStatus, summary="Alembic migrations status (Fase 12)")
async def get_migrations_status(db: AsyncSession = Depends(get_db)) -> MigrationsStatus:
    from app.db.migrations import head_revision

    head = head_revision()
    current = None
    try:
        result = await db.execute(text("SELECT version_num FROM alembic_version"))
        row = result.first()
        current = row[0] if row else None
    except Exception:
        current = None

    return MigrationsStatus(head=head, current=current, up_to_date=(current == head))
