"""
POST /api/v1/modules/{id}/verify — Runtime Integrity Verification
=====================================================================
Fase 10 §15/§20/§26 — reverifica integridade sob demanda. Não é
polling: chamado manualmente, no startup, ou depois de update.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.module_engine.registry import registry
from app.module_trust.verification import verify_module_integrity

router = APIRouter(prefix="/modules", tags=["module-trust"])


class IntegrityVerifyRead(BaseModel):
    module_id:         str
    status:            str
    modified_files:    list[str]
    missing_files:     list[str]
    unexpected_files:  list[str]


@router.post("/{module_id}/verify", response_model=IntegrityVerifyRead,
             summary="Reverify a module's integrity on demand (§15/§20)")
async def verify_module(module_id: str, db: AsyncSession = Depends(get_db)) -> IntegrityVerifyRead:
    if registry.get(module_id) is None:
        raise HTTPException(404, f"Module not found: {module_id!r}")

    result = await verify_module_integrity(module_id, db)
    return IntegrityVerifyRead(
        module_id=module_id, status=result.status.value,
        modified_files=result.modified_files, missing_files=result.missing_files,
        unexpected_files=result.unexpected_files,
    )
