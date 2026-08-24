"""
/api/v1/runtime/status — Runtime foundation (Phase 6)
======================================================
Exposes the runtime state for the Dashboard and the Launcher `status` command.
"""
from fastapi import APIRouter

from app.runtime import runtime

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/status", summary="Runtime state (Phase 6 foundation)")
async def get_runtime_status() -> dict:
    return runtime.status()
