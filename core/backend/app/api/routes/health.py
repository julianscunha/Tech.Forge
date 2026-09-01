"""
/api/v1/health — Module Health Checks
======================================
Exposes per-module health status.
Installed modules are evaluated through their runtime health_check() hook.
"""
import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.settings import settings
from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import registry
from app.module_runtime.state import RuntimeState, module_runtime_registry

router = APIRouter(prefix="/health", tags=["health"])


class ModuleHealth(BaseModel):
    module_id: str
    name:      str
    status:    ModuleStatus
    is_healthy: bool
    issues:    list[str]


class PlatformHealth(BaseModel):
    healthy_modules:   int
    unhealthy_modules: int
    modules: list[ModuleHealth]


async def _module_health(entry) -> ModuleHealth:
    issues = list(entry.errors)
    is_healthy = entry.status == ModuleStatus.INSTALLED

    if entry.status == ModuleStatus.INSTALLED:
        from app.module_runtime.lifecycle import health_check

        try:
            await asyncio.wait_for(
                health_check(entry.module_id, entry.entry_backend),
                timeout=settings.MODULE_HEALTH_CHECK_TIMEOUT,
            )
        except TimeoutError:
            module_runtime_registry.set_state(
                entry.module_id,
                RuntimeState.FAILED,
                last_error=f"health_check timed out after {settings.MODULE_HEALTH_CHECK_TIMEOUT}s",
            )

        runtime_entry = module_runtime_registry.get(entry.module_id)
        if runtime_entry is not None:
            is_healthy = runtime_entry.state == RuntimeState.READY
            if runtime_entry.last_error:
                issues.append(runtime_entry.last_error)

    return ModuleHealth(
        module_id=entry.module_id,
        name=entry.name,
        status=entry.status,
        is_healthy=is_healthy,
        issues=issues,
    )


@router.get("", response_model=PlatformHealth, summary="Platform-wide module health")
async def get_platform_health() -> PlatformHealth:
    modules = []
    for entry in registry.all():
        modules.append(await _module_health(entry))
    return PlatformHealth(
        healthy_modules=sum(1 for m in modules if m.is_healthy),
        unhealthy_modules=sum(1 for m in modules if not m.is_healthy),
        modules=modules,
    )


@router.get("/{module_id}", response_model=ModuleHealth)
async def get_module_health(module_id: str) -> ModuleHealth:
    entry = registry.get(module_id)
    if entry is None:
        raise HTTPException(404, detail=f"Module '{module_id}' not found in registry.")
    return await _module_health(entry)
