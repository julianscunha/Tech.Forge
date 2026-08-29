"""/api/v1/system — Fase 12 §24 (Persistence health).
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
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
