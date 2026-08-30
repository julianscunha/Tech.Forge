"""ErrorRegistryService — Fase 14 §19/§25."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_registry import ErrorRecord
from app.observability.diagnostic_codes import resolve_diagnostic_code


class ErrorRegistryService:

    @staticmethod
    async def record(
        db: AsyncSession,
        *,
        source: str,
        message: str,
        detail: Optional[str] = None,
        module_id: Optional[str] = None,
        execution_id: Optional[str] = None,
    ) -> ErrorRecord:
        diagnostic = resolve_diagnostic_code(source)
        entry = ErrorRecord(source=source, message=message, detail=detail,
                            module_id=module_id, execution_id=execution_id,
                            code=diagnostic.code if diagnostic else None)
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def recent(db: AsyncSession, limit: int = 50) -> Sequence[ErrorRecord]:
        stmt = select(ErrorRecord).order_by(ErrorRecord.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def list_for_module(db: AsyncSession, module_id: str, limit: int = 50) -> Sequence[ErrorRecord]:
        stmt = (select(ErrorRecord)
                .where(ErrorRecord.module_id == module_id)
                .order_by(ErrorRecord.created_at.desc())
                .limit(limit))
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def cleanup_old(db: AsyncSession, retention_days: int) -> int:
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        result = await db.execute(delete(ErrorRecord).where(ErrorRecord.created_at < cutoff))
        await db.commit()
        return result.rowcount or 0
