"""StorageProvider — Fase 12 §3/§24.

Formaliza acesso a saúde da persistência (engine já vive em `app.db.database`).
Não substitui `get_db`/`init_db` — só adiciona um probe de health reutilizável
pela API e pelo CLI.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class StorageHealth:
    database: bool
    writable: bool


class StorageProvider:
    async def health_check(self, db: AsyncSession) -> StorageHealth:
        try:
            await db.execute(text("SELECT 1"))
            database = True
        except Exception:
            return StorageHealth(database=False, writable=False)

        try:
            await db.execute(text("CREATE TEMP TABLE IF NOT EXISTS _storage_health_probe (x INTEGER)"))
            await db.execute(text("DROP TABLE _storage_health_probe"))
            writable = True
        except Exception:
            writable = False

        return StorageHealth(database=database, writable=writable)


storage_provider = StorageProvider()
