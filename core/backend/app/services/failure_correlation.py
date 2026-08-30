"""FailureCorrelationService — Fase 14 §17/§18.

Dado um erro do Error Registry, monta a cadeia Error → Module →
Execution → Dependency → eventos recentes, reaproveitando o que já
existe (Execution History, module_runtime_registry, dependency_engine,
OperationLog, RuntimeEvent) em vez de duplicar estado.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_registry import ErrorRecord
from app.models.execution_history import ExecutionHistory


class FailureCorrelationService:

    @staticmethod
    async def correlate(db: AsyncSession, error_id: int) -> Optional[dict[str, Any]]:
        error = await db.get(ErrorRecord, error_id)
        if error is None:
            return None

        execution = None
        if error.execution_id:
            stmt = select(ExecutionHistory).where(ExecutionHistory.execution_id == error.execution_id)
            row = (await db.execute(stmt)).scalar_one_or_none()
            if row is not None:
                execution = {
                    "execution_id": row.execution_id,
                    "status": row.status,
                    "duration_seconds": row.duration_seconds,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }

        module_runtime = None
        dependents: list[str] = []
        recent_operations: list[dict[str, Any]] = []
        if error.module_id:
            from app.module_runtime.state import module_runtime_registry
            entry = module_runtime_registry.get(error.module_id)
            if entry is not None:
                module_runtime = {
                    "state": entry.state.value,
                    "since": entry.since.isoformat(),
                    "last_error": entry.last_error,
                }

            from app.dependency_engine.lifecycle import _dependents_of
            from app.module_engine.registry import registry as module_registry
            from app.service_registry.registry import service_registry
            dependents = _dependents_of(error.module_id, module_registry, service_registry)

            from app.package_manager.operation_log import operation_log
            recent_operations = [
                {"operation": e.operation, "status": e.status, "message": e.message,
                 "timestamp": e.timestamp.isoformat()}
                for e in operation_log.for_module(error.module_id)[:5]
            ]

        from app.runtime import runtime
        recent_runtime_events = [e.as_dict() for e in runtime.events[-5:]]

        return {
            "error": {
                "id": error.id,
                "source": error.source,
                "code": error.code,
                "message": error.message,
                "detail": error.detail,
                "module_id": error.module_id,
                "execution_id": error.execution_id,
                "created_at": error.created_at.isoformat() if error.created_at else None,
            },
            "execution": execution,
            "module_runtime": module_runtime,
            "dependents": dependents,
            "recent_operations": recent_operations,
            "recent_runtime_events": recent_runtime_events,
        }
