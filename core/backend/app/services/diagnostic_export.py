"""DiagnosticExportService — Fase 14 §29.

Monta um snapshot completo (System Diagnostics + startup + erros e
execuções recentes) e formata em JSON ou TXT. ZIP support bundle fica
pro slice seguinte (§30) — este aqui é só o "Diagnostic Report" simples
que o spec pede primeiro.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.observability.startup_diagnostics import startup_diagnostics
from app.services.error_registry import ErrorRegistryService
from app.services.execution_history import ExecutionHistoryService
from app.services.system_diagnostics import SystemDiagnosticService


class DiagnosticExportService:

    @staticmethod
    async def build_snapshot(db: AsyncSession) -> dict[str, Any]:
        system = await SystemDiagnosticService.snapshot(db)
        errors = await ErrorRegistryService.recent(db, limit=20)
        executions = await ExecutionHistoryService.recent(db, limit=20)

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "platform_version": settings.PLATFORM_VERSION,
            "system": system,
            "startup": startup_diagnostics.snapshot(),
            "recent_errors": [
                {
                    "id": e.id, "source": e.source, "code": e.code, "message": e.message,
                    "module_id": e.module_id, "execution_id": e.execution_id,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in errors
            ],
            "recent_executions": [
                {
                    "execution_id": ex.execution_id, "module_id": ex.module_id, "status": ex.status,
                    "duration_seconds": ex.duration_seconds,
                    "created_at": ex.created_at.isoformat() if ex.created_at else None,
                }
                for ex in executions
            ],
        }

    @staticmethod
    def to_json(snapshot: dict[str, Any]) -> str:
        return json.dumps(snapshot, indent=2, ensure_ascii=False)

    @staticmethod
    def to_txt(snapshot: dict[str, Any]) -> str:
        lines = [
            f"TechForge Diagnostic Report — {snapshot['generated_at']}",
            f"Platform version: {snapshot['platform_version']}",
            "",
            "== System ==",
            f"Database: {snapshot['system']['platform']['database_status']}",
            f"Modules installed: {snapshot['system']['platform']['modules_installed']}"
            f" (enabled: {snapshot['system']['platform']['modules_enabled']})",
            f"Runtime state: {snapshot['system']['runtime']['state']}",
            "",
            "== Startup ==",
            f"Total: {snapshot['startup']['total_seconds']}s",
        ]
        for step, duration in snapshot["startup"]["steps"].items():
            lines.append(f"  {step}: {duration}s")

        lines += ["", f"== Recent errors ({len(snapshot['recent_errors'])}) =="]
        for err in snapshot["recent_errors"]:
            lines.append(f"  [{err['code'] or err['source']}] {err['message']} (module={err['module_id']})")

        lines += ["", f"== Recent executions ({len(snapshot['recent_executions'])}) =="]
        for ex in snapshot["recent_executions"]:
            lines.append(f"  {ex['module_id']}: {ex['status']} ({ex['duration_seconds']}s)")

        return "\n".join(lines) + "\n"
