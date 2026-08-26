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

import os
import sys
from datetime import datetime
from enum import Enum
from typing import Callable, Optional


def current_frontend_mode(dist_path: Optional["object"] = None) -> str:
    """Modo de entrega do frontend (§14): static | dev | none.

    static: SERVE_STATIC_FRONTEND=true e dist/index.html existe.
    dev:    flag off (launcher sobe o vite dev server).
    none:   flag on mas sem build disponível.
    """
    from app.core.settings import settings  # import tardio evita ciclo
    dist = dist_path if dist_path is not None else settings.FRONTEND_DIST_PATH
    serve = bool(getattr(settings, "SERVE_STATIC_FRONTEND", False))
    has_build = (dist / "index.html").is_file()
    if serve and has_build:
        return "static"
    if serve:
        return "none"
    return "dev"


class RuntimeState(str, Enum):
    BOOTSTRAPPING = "bootstrapping"
    READY = "ready"
    DEGRADED = "degraded"      # §15 — componente registrado morreu
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
        self._component_pids: dict[str, int] = {}
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

    # ── Component supervision (§14/§15) ───────────────────────────────────────

    def register_component_pid(self, component: str, pid: int) -> None:
        """Launcher informa o PID de um componente que ele iniciou."""
        self._component_pids[component] = pid

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:   # existe mas é de outro usuário
            return True
        except OSError:
            # Windows: os.kill(pid, 0) lança OSError para PID inexistente
            # com AccessViolation em alguns casos — tratar via OpenProcess.
            if sys.platform == "win32":
                import ctypes
                handle = ctypes.windll.kernel32.OpenProcess(0x100000, False, pid)
                if not handle:
                    return False
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return True

    def check_liveness(self) -> dict[str, bool]:
        """Checagem on-demand dos PIDs registrados; marca DEGRADED se morto."""
        result = {}
        for name, pid in self._component_pids.items():
            alive = self._pid_alive(pid)
            result[name] = alive
            if not alive and self.state in (RuntimeState.READY, RuntimeState.BOOTSTRAPPING):
                self.state = RuntimeState.DEGRADED
                self.events.append(RuntimeEvent("degraded", f"{name} (pid {pid}) não está mais em execução"))
        return result

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> dict:
        uptime: Optional[float] = None
        if self.started_at is not None:
            uptime = max(0.0, (datetime.utcnow() - self.started_at).total_seconds())
        liveness = self.check_liveness() if self._component_pids else {}
        return {
            "state": self.state.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "uptime_seconds": uptime,
            "frontend_mode": current_frontend_mode(),
            "components": liveness,
            "events": [e.as_dict() for e in self.events[-20:]],
        }


runtime = TechForgeRuntime()
