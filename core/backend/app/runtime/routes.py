"""
/api/v1/runtime/status — Runtime foundation (Phase 6)
/api/v1/runtime/modules[/...] — Module Runtime (Fase 9 §26)
================================================================
Exposes the platform-wide runtime state (Phase 6) plus per-module Runtime
State (Fase 9) for the Dashboard, Developer Center, and the CLI.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.runtime import runtime

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/status", summary="Runtime state (Phase 6 foundation)")
async def get_runtime_status() -> dict:
    return runtime.status()


# ── Module Runtime (Fase 9 §23/§26) ────────────────────────────────────────────

class ModuleRuntimeRead(BaseModel):
    module_id:      str
    state:          str
    last_error:     Optional[str]
    last_execution: Optional[str]
    uptime_seconds: Optional[float]


def _to_read(entry) -> ModuleRuntimeRead:
    from app.module_runtime.state import module_runtime_registry
    return ModuleRuntimeRead(
        module_id=entry.module_id,
        state=entry.state.value,
        last_error=entry.last_error,
        last_execution=entry.last_execution.isoformat() if entry.last_execution else None,
        uptime_seconds=module_runtime_registry.uptime_seconds(entry.module_id),
    )


@router.get("/modules", response_model=list[ModuleRuntimeRead],
            summary="Runtime State of every INSTALLED module (§23)")
async def list_module_runtime() -> list[ModuleRuntimeRead]:
    from app.module_runtime.state import module_runtime_registry
    return [_to_read(e) for e in module_runtime_registry.list_all()]


@router.get("/modules/{module_id}", response_model=ModuleRuntimeRead,
            summary="Runtime State of one module (§23)")
async def get_module_runtime(module_id: str) -> ModuleRuntimeRead:
    from app.module_runtime.state import module_runtime_registry
    entry = module_runtime_registry.get(module_id)
    if entry is None:
        raise HTTPException(404, f"No Runtime State for module: {module_id!r}")
    return _to_read(entry)


@router.post("/modules/{module_id}/initialize", response_model=ModuleRuntimeRead,
             summary="Re-run health_check() on demand (§10/§18) — reuses Slice 3, no cache")
async def initialize_module_runtime(module_id: str) -> ModuleRuntimeRead:
    from app.module_engine.registry import registry as module_registry
    from app.module_runtime.lifecycle import health_check
    from app.module_runtime.state import module_runtime_registry

    entry = module_registry.get(module_id)
    if entry is None:
        raise HTTPException(404, f"Module not found: {module_id!r}")

    await health_check(module_id, entry.entry_backend)
    runtime_entry = module_runtime_registry.get(module_id)
    if runtime_entry is None:
        raise HTTPException(409, f"Module '{module_id}' has no Runtime State (not INSTALLED)")
    return _to_read(runtime_entry)
