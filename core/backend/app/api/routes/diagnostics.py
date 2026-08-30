"""/api/v1/diagnostics*, /api/v1/modules/{id}/diagnostics|executions —
Fase 14 §34.

Só leitura — reaproveita os services já existentes (SystemDiagnosticService,
ErrorRegistryService, ExecutionHistoryService, DiagnosticExportService,
SupportBundleService), nenhuma lógica nova aqui. "Evitar expor logs
completos sem limites" (§34) — paginação/limite em toda listagem.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.diagnostic_export import DiagnosticExportService
from app.services.error_registry import ErrorRegistryService
from app.services.execution_history import ExecutionHistoryService
from app.services.heaviest_modules import HeaviestModulesService
from app.services.resource_usage import ResourceUsageService
from app.services.support_bundle import SupportBundleService
from app.services.system_diagnostics import SystemDiagnosticService

diagnostics_router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])
modules_diagnostics_router = APIRouter(prefix="/modules", tags=["diagnostics"])


@diagnostics_router.get("", summary="Full system diagnostics snapshot")
async def get_diagnostics(db: AsyncSession = Depends(get_db)) -> dict:
    return await SystemDiagnosticService.snapshot(db)


@diagnostics_router.get("/health", summary="Platform + storage + runtime health")
async def get_diagnostics_health(db: AsyncSession = Depends(get_db)) -> dict:
    snapshot = await SystemDiagnosticService.snapshot(db)
    return {"platform": snapshot["platform"], "storage": snapshot["storage"], "runtime": snapshot["runtime"]}


@diagnostics_router.get("/errors", summary="Recent errors (Error Registry)")
async def get_diagnostics_errors(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    entries = await ErrorRegistryService.recent(db, limit=limit)
    return [
        {"id": e.id, "source": e.source, "code": e.code, "message": e.message,
         "detail": e.detail, "module_id": e.module_id, "execution_id": e.execution_id,
         "created_at": e.created_at.isoformat() if e.created_at else None}
        for e in entries
    ]


@diagnostics_router.get("/executions", summary="Recent module executions")
async def get_diagnostics_executions(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    entries = await ExecutionHistoryService.recent(db, limit=limit)
    return [
        {"execution_id": e.execution_id, "module_id": e.module_id, "status": e.status,
         "duration_seconds": e.duration_seconds, "error_summary": e.error_summary,
         "created_at": e.created_at.isoformat() if e.created_at else None}
        for e in entries
    ]


@diagnostics_router.get("/resources", summary="CPU/memory/disk usage of the Core process")
async def get_diagnostics_resources() -> dict:
    return ResourceUsageService.snapshot()


@diagnostics_router.get("/heaviest-modules", summary="Modules ranked by disk footprint")
async def get_heaviest_modules(
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await HeaviestModulesService.snapshot(db, limit=limit)


@diagnostics_router.post("/export", summary="Export a Diagnostic Report or Support Bundle")
async def export_diagnostics(
    format: str = Query(default="json", pattern="^(json|txt|zip)$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    if format == "zip":
        data = await SupportBundleService.build_zip(db)
        return Response(content=data, media_type="application/zip",
                        headers={"Content-Disposition": "attachment; filename=techforge-support-bundle.zip"})

    snapshot = await DiagnosticExportService.build_snapshot(db)
    if format == "txt":
        return PlainTextResponse(DiagnosticExportService.to_txt(snapshot))
    return Response(content=DiagnosticExportService.to_json(snapshot), media_type="application/json")


@modules_diagnostics_router.get("/{module_id}/diagnostics", summary="Diagnostics for a single module")
async def get_module_diagnostics(module_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    from app.module_runtime.state import module_runtime_registry

    entry = module_runtime_registry.get(module_id)
    errors = await ErrorRegistryService.list_for_module(db, module_id, limit=20)
    executions = await ExecutionHistoryService.list_for_module(db, module_id, limit=20)

    return {
        "module_id": module_id,
        "runtime": {
            "state": entry.state.value, "since": entry.since.isoformat(),
            "last_error": entry.last_error,
            "last_execution": entry.last_execution.isoformat() if entry.last_execution else None,
        } if entry else None,
        "recent_errors": [
            {"id": e.id, "code": e.code, "message": e.message,
             "created_at": e.created_at.isoformat() if e.created_at else None}
            for e in errors
        ],
        "recent_executions": [
            {"execution_id": e.execution_id, "status": e.status, "duration_seconds": e.duration_seconds,
             "created_at": e.created_at.isoformat() if e.created_at else None}
            for e in executions
        ],
    }


@modules_diagnostics_router.get("/{module_id}/executions", summary="Execution history for a single module")
async def get_module_executions(
    module_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    entries = await ExecutionHistoryService.list_for_module(db, module_id, limit=limit)
    return [
        {"execution_id": e.execution_id, "status": e.status, "duration_seconds": e.duration_seconds,
         "error_summary": e.error_summary, "created_at": e.created_at.isoformat() if e.created_at else None}
        for e in entries
    ]
