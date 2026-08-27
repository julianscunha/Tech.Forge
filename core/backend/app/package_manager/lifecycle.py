"""Fase 4 §9/§10 — Activate / Deactivate service.

Semântica (diretriz do usuário): disable = poupar recursos.
- deactivate: grava flag disabled em <module>/data/state.json + is_enabled=False no DB
  → o Loader não monta entry_backend de módulos DISABLED no boot
  → NavigationBuilder exclui módulos DISABLED
- activate: limpa a flag, is_enabled=True, re-registra como INSTALLED e monta rotas

Operações são registradas no operation_log e geram notificações.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import registry
from app.models.registry import Module
from app.package_manager import operation_log
from app.services.notifications import NotificationService

logger = logging.getLogger("techforge.package_manager.lifecycle")

_STATE_FILE = "data/state.json"


def _state_path(module_id: str) -> Path:
    return settings.MODULES_INSTALLED_PATH / module_id / _STATE_FILE


def _read_disabled_flag(module_id: str) -> bool:
    state_file = _state_path(module_id)
    if not state_file.is_file():
        return False
    try:
        return bool(json.loads(state_file.read_text(encoding="utf-8")).get("disabled", False))
    except (OSError, ValueError):
        return False


def _write_disabled_flag(module_id: str, disabled: bool) -> None:
    state_file = _state_path(module_id)
    state: dict = {}
    if state_file.is_file():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8")) or {}
        except (OSError, ValueError):
            state = {}
    state["disabled"] = disabled
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


async def _set_db_enabled(db: AsyncSession, module_id: str, enabled: bool) -> None:
    await db.execute(
        sa_update(Module).where(Module.module_id == module_id).values(is_enabled=enabled)
    )
    await db.commit()


async def _notify(db: AsyncSession, level: str, title: str, message: str,
                  module_id: str) -> None:
    try:
        await NotificationService.create(
            db, level=level, title=title, message=message, module_id=module_id,
        )
    except Exception:  # notification must never break the lifecycle operation
        logger.warning("Failed to create lifecycle notification for %s", module_id)


async def deactivate_module(db: AsyncSession, module_id: str) -> dict:
    """INSTALLED → DISABLED. Files preserved; module skipped at next boot."""
    entry = registry.get(module_id)
    target_dir = settings.MODULES_INSTALLED_PATH / module_id

    if entry is None or not target_dir.is_dir():
        return {"ok": False, "status": 404, "detail": f"Module '{module_id}' not found"}
    if entry.status == ModuleStatus.DISABLED or _read_disabled_flag(module_id):
        return {"ok": False, "status": 409,
                "detail": f"Module '{module_id}' is already disabled"}

    registry.set_status(module_id, ModuleStatus.DISABLED)
    _write_disabled_flag(module_id, True)
    await _set_db_enabled(db, module_id, False)
    from app.doc_engine import doc_indexer
    from app.service_registry.registry import sync_with_notifications
    await sync_with_notifications(registry.all(), doc_indexer, db)
    operation_log.record("deactivate", module_id,
                         entry.version, "success", "Module deactivated")

    await _notify(db, "warning", f"Módulo desativado: {entry.name}",
                 f"{module_id} v{entry.version} foi desativado e não consome recursos.",
                 module_id)

    logger.info("Module deactivated: %s", module_id)
    return {"ok": True, "status": 200,
            "message": f"Module '{module_id}' deactivated", "status_value": "DISABLED"}


async def activate_module(db: AsyncSession, module_id: str) -> dict:
    """DISABLED → INSTALLED. Clears the flag and hot-mounts the backend router."""
    entry = registry.get(module_id)
    target_dir = settings.MODULES_INSTALLED_PATH / module_id

    if entry is None or not target_dir.is_dir():
        return {"ok": False, "status": 404, "detail": f"Module '{module_id}' not found"}
    if entry.status != ModuleStatus.DISABLED:
        return {"ok": False, "status": 409,
                "detail": f"Module '{module_id}' is not disabled"}

    registry.set_status(module_id, ModuleStatus.INSTALLED)
    _write_disabled_flag(module_id, False)
    await _set_db_enabled(db, module_id, True)
    operation_log.record("activate", module_id,
                         entry.version, "success", "Module activated")

    # Hot activation — mounting routers on demand is safe and cheap
    try:
        from app.module_engine.plugin_loader import mount_module_routers
        from app.main import app
        mount_module_routers(app)
    except Exception as exc:
        logger.warning("Hot mount after activation failed for %s: %s", module_id, exc)

    from app.doc_engine import doc_indexer
    from app.service_registry.registry import sync_with_notifications
    await sync_with_notifications(registry.all(), doc_indexer, db)

    await _notify(db, "success", f"Módulo ativado: {entry.name}",
                  f"{module_id} v{entry.version} está ativo novamente.", module_id)

    logger.info("Module activated: %s", module_id)
    return {"ok": True, "status": 200,
            "message": f"Module '{module_id}' activated", "status_value": "INSTALLED"}
