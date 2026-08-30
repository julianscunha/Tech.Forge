"""/api/v1/modules/{id}/quality|release-readiness — Fase 15 §44/§45."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.module_quality import ModuleNotFoundError, compute_module_quality

router = APIRouter(prefix="/modules", tags=["modules"])


class ModuleCheckRead(BaseModel):
    name: str
    passed: bool
    detail: str


class ModuleQualityRead(BaseModel):
    module_id: str
    ready: bool
    checks: list[ModuleCheckRead]


def _report_to_read(module_id: str, report) -> ModuleQualityRead:
    return ModuleQualityRead(
        module_id=module_id,
        ready=report.ready,
        checks=[ModuleCheckRead(name=c.name, passed=c.passed, detail=c.detail) for c in report.checks],
    )


@router.get("/{module_id}/quality", response_model=ModuleQualityRead)
async def get_module_quality(module_id: str) -> ModuleQualityRead:
    try:
        report = compute_module_quality(module_id)
    except ModuleNotFoundError:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found.")
    return _report_to_read(module_id, report)


@router.get("/{module_id}/release-readiness", response_model=ModuleQualityRead)
async def get_module_release_readiness(module_id: str) -> ModuleQualityRead:
    # Mesma computação de /quality, reframed como gate de release — não
    # duplica lógica (spec §2: "não criar critérios paralelos de qualidade").
    try:
        report = compute_module_quality(module_id)
    except ModuleNotFoundError:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found.")
    return _report_to_read(module_id, report)
