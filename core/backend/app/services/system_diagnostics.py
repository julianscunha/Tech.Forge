"""SystemDiagnosticService — Fase 14 §15.

Consolida Health (Fase 1) + Storage (Fase 12) + Runtime (Fase 6) + Module
Health (Fase 9) num serviço único — sem inventar um `/ready` novo (não se
aplica a Desktop single-instância; ver decisão registrada em
tasks/phase14-plan.md).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paths import install_dir, user_data_dir
from app.core.settings import settings
from app.module_runtime.state import module_runtime_registry
from app.runtime import runtime
from app.services.registry import CategoryService, ModuleService


class SystemDiagnosticService:

    @staticmethod
    async def snapshot(db: AsyncSession) -> dict[str, Any]:
        try:
            await db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:
            db_status = "error"

        from app.db.storage import storage_provider
        storage_health = await storage_provider.health_check(db)

        return {
            "platform": {
                "name": settings.PLATFORM_NAME,
                "version": settings.PLATFORM_VERSION,
                "database_status": db_status,
                "modules_installed": await ModuleService.count_installed(db),
                "modules_enabled": await ModuleService.count_enabled(db),
                "categories_registered": await CategoryService.count(db),
                "paths": {  # Fase 16 §38 — só exibido na UI quando Developer Mode está ativo
                    "install_dir": str(install_dir()),
                    "user_data_dir": str(user_data_dir()),
                },
            },
            "storage": {
                "database": storage_health.database,
                "writable": storage_health.writable,
            },
            "runtime": runtime.status(),
            "modules": [
                {
                    "module_id": entry.module_id,
                    "state": entry.state.value,
                    "since": entry.since.isoformat(),
                    "last_error": entry.last_error,
                    "last_execution": entry.last_execution.isoformat() if entry.last_execution else None,
                }
                for entry in module_runtime_registry.list_all()
            ],
        }
