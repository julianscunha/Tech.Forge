"""
TechForge Runtime (Phase 6 — foundation)
========================================
Minimal runtime foundation. Future phases will extend this to own the
module execution lifecycle (dependencies, service registry, dynamic
activation). For now it only:

  - knows the platform state (bootstrap → ready → shutting_down → stopped)
  - receives startup/shutdown events and timestamps them
  - exposes state via GET /api/v1/runtime/status for the Dashboard

It deliberately does NOT duplicate the Module Registry, Package Manager,
Documentation Engine, or logging system.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Callable, Optional


class RuntimeState(str, Enum):
    BOOTSTRAPPING = "bootstrapping"
    READY = "ready"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


class RuntimeEvent:
    """One lifecycle event received by the runtime."""

    def __init__(self, name: str, detail: str = "") -> None:
        self.timestamp = datetime.utcnow()
        self.name = name
        self.detail = detail

    def as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "name": self.name,
            "detail": self.detail,
        }


class TechForgeRuntime:
    """
    Process-lifetime singleton holding platform run state.

    Usage (FastAPI lifespan):
        await runtime.fire_startup("backend started")
        ...
        await runtime.fire_shutdown("platform stopped")
    """

    def __init__(self) -> None:
        self.state: RuntimeState = RuntimeState.BOOTSTRAPPING
        self.started_at: Optional[datetime] = None
        self.events: list[RuntimeEvent] = []
        self._startup_handlers: list[Callable[[RuntimeEvent], None]] = []
        self._shutdown_handlers: list[Callable[[RuntimeEvent], None]] = []

    # ── Handlers (foundation for future module hooks) ─────────────────────────

    def on_startup(self, handler: Callable[[RuntimeEvent], None]) -> None:
        self._startup_handlers.append(handler)

    def on_shutdown(self, handler: Callable[[RuntimeEvent], None]) -> None:
        self._shutdown_handlers.append(handler)

    # ── Lifecycle events ───────────────────────────────────────────────────────

    async def fire_startup(self, detail: str = "") -> None:
        event = RuntimeEvent("startup", detail)
        self.events.append(event)
        if self.state is RuntimeState.BOOTSTRAPPING:
            self.state = RuntimeState.READY
            self.started_at = event.timestamp

    async def fire_shutdown(self, detail: str = "") -> None:
        event = RuntimeEvent("shutdown", detail)
        self.events.append(event)
        self.state = RuntimeState.STOPPED
        for handler in self._shutdown_handlers:
            try:
                handler(event)
            except Exception:  # a failing hook must never block shutdown
                pass

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> dict:
        return {
            "state": self.state.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "events": [e.as_dict() for e in self.events[-20:]],
        }


runtime = TechForgeRuntime()
