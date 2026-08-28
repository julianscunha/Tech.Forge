"""
Plugin Loader (Phase 2+)
========================
Dynamically mounts module backend routers into the running FastAPI app.

For every module with status INSTALLED in the ModuleRegistry, this loader:
  1. Reads `entry_backend` from the ModuleEntry
  2. Imports `<module_dir>/<entry_backend>` as a Python module
  3. Looks for a FastAPI `router` attribute and mounts it under /api/v1

Mount path convention: modules declare their own prefix in the router
(e.g. APIRouter(prefix="/modules/hello_world")), which becomes
/api/v1/modules/hello_world/... once mounted.

Failures are non-fatal: a broken module router is logged into the loader
journal as an error event and skipped, never crashing the platform.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from fastapi import FastAPI

from app.core.settings import settings
from app.module_engine import journal as loader_journal
from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import registry
from app.module_runtime.loader import ModuleLoadError, load_module_file

logger = logging.getLogger("techforge.plugin_loader")

# Módulos já montados nesta instância do app — garante idempotência de
# mount_module_routers (sem rotas duplicadas em re-ativação).
_mounted_module_ids: set[str] = set()


@dataclass
class MountResult:
    """Summary of one plugin-loader pass."""
    mounted: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)  # module_id → error


def _import_router(module_id: str, entry_backend: str):
    """
    Import `entry_backend` from an installed module directory and return its
    FastAPI `router` attribute.

    The module file is loaded by explicit file path so it does not need to be
    on sys.path and cannot collide with core packages.
    """
    module_dir = settings.MODULES_INSTALLED_PATH / module_id
    entry_path = module_dir / entry_backend
    import_name = f"techforge_modules.{module_id}.backend"

    try:
        py_module = load_module_file(import_name, entry_path)
    except ModuleLoadError as exc:
        raise ImportError(str(exc)) from exc

    router = getattr(py_module, "router", None)
    if router is None:
        raise AttributeError(
            f"{entry_backend} does not export a FastAPI `router`"
        )
    return router


def mount_module_routers(app: FastAPI) -> MountResult:
    """
    Mount the router of every INSTALLED module onto the app.

    Called from the FastAPI lifespan AFTER ModuleLoader.scan_installed(),
    so the registry is already populated.

    Idempotent: modules already mounted (tracked by module_id) are skipped,
    so calling this again (e.g. after activate_module) only mounts the delta
    and never registers duplicate routes.
    """
    result = MountResult()

    for entry in registry.by_status(ModuleStatus.INSTALLED):
        if entry.module_id in _mounted_module_ids:
            continue
        try:
            router = _import_router(entry.module_id, entry.entry_backend)
            app.include_router(router, prefix="/api/v1")
            _mounted_module_ids.add(entry.module_id)
            logger.info(
                "Plugin Loader: mounted router for '%s' at /api/v1%s",
                entry.module_id,
                getattr(router, "prefix", ""),
            )
            loader_journal.add_event(
                f"Router mounted at /api/v1{getattr(router, 'prefix', '')}",
                level="info",
                module_id=entry.module_id,
                details={"entry_backend": entry.entry_backend},
            )
        except Exception as exc:  # noqa: BLE001 — a broken module must not crash the platform
            result.failed[entry.module_id] = str(exc)
            logger.warning(
                "Plugin Loader: failed to mount router for '%s': %s",
                entry.module_id, exc,
            )
            loader_journal.add_event(
                f"Failed to mount backend router: {exc}",
                level="error",
                module_id=entry.module_id,
                details={"entry_backend": entry.entry_backend},
            )

    return result
