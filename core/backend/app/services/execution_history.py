"""ExecutionHistoryService — Fase 14 §23.

Registra e consulta o histórico de execuções de módulo. Retenção
configurável (não infinita — spec §9/§37 aplicado aqui também).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_history import ExecutionHistory


class ExecutionHistoryService:

    @staticmethod
    async def record(
        db: AsyncSession,
        *,
        execution_id: str,
        module_id: str,
        status: str,
        duration_seconds: float,
        error_summary: Optional[str] = None,
    ) -> ExecutionHistory:
        entry = ExecutionHistory(
            execution_id=execution_id, module_id=module_id, status=status,
            duration_seconds=duration_seconds, error_summary=error_summary,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def list_for_module(db: AsyncSession, module_id: str, limit: int = 50) -> Sequence[ExecutionHistory]:
        stmt = (select(ExecutionHistory)
                .where(ExecutionHistory.module_id == module_id)
                .order_by(ExecutionHistory.created_at.desc())
                .limit(limit))
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def recent(db: AsyncSession, limit: int = 50) -> Sequence[ExecutionHistory]:
        stmt = select(ExecutionHistory).order_by(ExecutionHistory.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def cleanup_old(db: AsyncSession, retention_days: int) -> int:
        # naive UTC — combina com server_default=func.now() do SQLite (sem tz)
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        result = await db.execute(delete(ExecutionHistory).where(ExecutionHistory.created_at < cutoff))
        await db.commit()
        return result.rowcount or 0
