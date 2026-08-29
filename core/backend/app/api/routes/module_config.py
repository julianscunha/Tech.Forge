"""/api/v1/modules/{id}/config — Fase 12 §10/§12/§29.

Fonte dos campos declarados é o registry in-memory (manifest_raw), a
mesma fonte única de verdade usada por todas as outras APIs de módulo
(ver CLAUDE.md) — nunca reparseia manifest.yaml do disco aqui.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.module_engine.manifest import parse_configuration_fields
from app.module_engine.registry import registry
from app.services.module_configuration import ConfigValidationError, get_config, save_config, validate_config

router = APIRouter(prefix="/modules", tags=["modules"])


class ModuleConfigRead(BaseModel):
    module_id: str
    values: dict[str, Any]


class ModuleConfigWrite(BaseModel):
    values: dict[str, Any]


def _fields_for(module_id: str):
    entry = registry.get(module_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found.")
    return parse_configuration_fields(entry.manifest_raw)


@router.get("/{module_id}/config", response_model=ModuleConfigRead)
async def get_module_config(module_id: str, db: AsyncSession = Depends(get_db)) -> ModuleConfigRead:
    fields = _fields_for(module_id)
    values = await get_config(db, module_id, fields)
    return ModuleConfigRead(module_id=module_id, values=values)


@router.put("/{module_id}/config", response_model=ModuleConfigRead)
async def put_module_config(
    module_id: str, payload: ModuleConfigWrite, db: AsyncSession = Depends(get_db)
) -> ModuleConfigRead:
    fields = _fields_for(module_id)
    try:
        values = await save_config(db, module_id, fields, payload.values)
    except ConfigValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors)
    return ModuleConfigRead(module_id=module_id, values=values)


@router.post("/{module_id}/config/validate")
async def validate_module_config(module_id: str, payload: ModuleConfigWrite) -> dict:
    fields = _fields_for(module_id)
    try:
        values = validate_config(fields, payload.values)
    except ConfigValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors)
    return {"valid": True, "values": values}
