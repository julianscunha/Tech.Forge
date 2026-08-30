"""
/api/v1/health — Module Health Checks
======================================
Exposes per-module health status.
In Phase 5 each module will supply its own health_check() method;
for now, health is derived from the registry status.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import registry

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


@router.get("", response_model=PlatformHealth, summary="Platform-wide module health")
async def get_platform_health() -> PlatformHealth:
    modules = []
    for entry in registry.all():
        modules.append(ModuleHealth(
            module_id=entry.module_id,
            name=entry.name,
            status=entry.status,
            is_healthy=entry.status == ModuleStatus.INSTALLED,
            issues=entry.errors,
        ))
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
    return ModuleHealth(
        module_id=entry.module_id,
        name=entry.name,
        status=entry.status,
        is_healthy=entry.status == ModuleStatus.INSTALLED,
        issues=entry.errors,
    )
