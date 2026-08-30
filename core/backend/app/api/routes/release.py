"""/api/v1/release — Release Readiness (Fase 15 §36/§37)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.release_readiness import compute_release_readiness

router = APIRouter(prefix="/release", tags=["release"])


class ReleaseCheckRead(BaseModel):
    name: str
    passed: bool
    detail: str


class ReleaseReadinessRead(BaseModel):
    version: str
    ready: bool
    checks: list[ReleaseCheckRead]


@router.get("/readiness", response_model=ReleaseReadinessRead, summary="Release Readiness Report (Fase 15)")
async def get_release_readiness(db: AsyncSession = Depends(get_db)) -> ReleaseReadinessRead:
    report = await compute_release_readiness(db)
    return ReleaseReadinessRead(
        version=report.version,
        ready=report.ready,
        checks=[ReleaseCheckRead(name=c.name, passed=c.passed, detail=c.detail) for c in report.checks],
    )
