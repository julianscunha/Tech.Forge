"""HeaviestModulesService — Fase 14 Slice 18 (Dashboard).

"Qual módulo é mais pesado" via proxy real e barato — espaço em disco
(exato) + duração média de execução + taxa de falha (já coletados pelo
Execution History). Não tenta atribuir CPU/memória por módulo: eles
rodam no mesmo processo/heap/GIL do Core, então essa medida não seria
confiável sem reabrir o module_runtime inteiro (fora de escopo, decisão
já registrada em tasks/phase14-plan.md).
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.execution_history import ExecutionHistory


def _dir_size_bytes(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


class HeaviestModulesService:

    @staticmethod
    async def snapshot(db: AsyncSession, limit: int = 5) -> list[dict]:
        stmt = (
            select(
                ExecutionHistory.module_id,
                func.avg(ExecutionHistory.duration_seconds).label("avg_duration"),
                func.count().label("total"),
                func.sum(case((ExecutionHistory.status == "FAILED", 1), else_=0)).label("failures"),
            )
            .group_by(ExecutionHistory.module_id)
        )
        rows = (await db.execute(stmt)).all()

        results = []
        for module_id, avg_duration, total, failures in rows:
            module_dir = settings.MODULES_INSTALLED_PATH / module_id
            results.append({
                "module_id": module_id,
                "disk_bytes": _dir_size_bytes(module_dir),
                "avg_duration_seconds": round(avg_duration or 0.0, 4),
                "execution_count": total,
                "failure_rate": round((failures or 0) / total, 4) if total else 0.0,
            })

        results.sort(key=lambda r: r["disk_bytes"], reverse=True)
        return results[:limit]
