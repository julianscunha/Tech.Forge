"""
Runtime State — Fase 9 §4/§5/§29 Slice 2
============================================
Separado do Administrative State (`ModuleStatus`, module_engine/enums.py):
administrativo é a decisão do usuário/operador (INSTALLED/DISABLED/
BLOCKED/...); Runtime State é o estado efêmero de execução, nunca
persistido — reconstruído a cada boot a partir do Administrative State.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable, Optional

from app.module_engine.enums import ModuleStatus


class RuntimeState(str, Enum):
    READY        = "READY"
    INITIALIZING = "INITIALIZING"
    EXECUTING    = "EXECUTING"
    DEGRADED     = "DEGRADED"
    FAILED       = "FAILED"
    STOPPED      = "STOPPED"


@dataclass
class ModuleRuntimeEntry:
    module_id:       str
    state:           RuntimeState
    since:           datetime
    last_error:      Optional[str] = None
    last_execution:  Optional[datetime] = None


class ModuleRuntimeRegistry:
    """
    In-memory, singleton, reconstruível — mesmo padrão de fonte única de
    verdade do `ServiceRegistry` (Fase 8). Só módulos administrativamente
    INSTALLED entram aqui: DISABLED/BLOCKED/INVALID/INCOMPATIBLE não têm
    Runtime State (não faz sentido "pronto pra executar" pra um módulo que
    não está ativo).
    """

    def __init__(self) -> None:
        self._entries: dict[str, ModuleRuntimeEntry] = {}

    def rebuild(self, module_entries: Iterable) -> None:
        """Reconstrói a partir do Administrative State — preserva histórico
        (last_error/last_execution) de módulos que continuam INSTALLED."""
        entries: dict[str, ModuleRuntimeEntry] = {}
        for entry in module_entries:
            if entry.status != ModuleStatus.INSTALLED:
                continue
            existing = self._entries.get(entry.module_id)
            entries[entry.module_id] = existing or ModuleRuntimeEntry(
                module_id=entry.module_id, state=RuntimeState.READY,
                since=datetime.now(timezone.utc),
            )
        self._entries = entries

    def clear_transient_state(self) -> None:
        """§27 — shutdown limpa o estado em memória, nunca dados persistidos."""
        self._entries = {}

    def get(self, module_id: str) -> Optional[ModuleRuntimeEntry]:
        return self._entries.get(module_id)

    def list_all(self) -> list[ModuleRuntimeEntry]:
        return list(self._entries.values())

    def set_state(self, module_id: str, state: RuntimeState,
                  last_error: Optional[str] = None) -> ModuleRuntimeEntry:
        """Cria a entrada se ainda não existir (ex: módulo recém-ativado)."""
        entry = self._entries.get(module_id)
        if entry is None:
            entry = ModuleRuntimeEntry(
                module_id=module_id, state=state, since=datetime.now(timezone.utc),
            )
            self._entries[module_id] = entry
        else:
            entry.state = state
            entry.since = datetime.now(timezone.utc)
        if last_error is not None:
            entry.last_error = last_error
        return entry

    def mark_executed(self, module_id: str) -> None:
        entry = self._entries.get(module_id)
        if entry is not None:
            entry.last_execution = datetime.now(timezone.utc)

    def uptime_seconds(self, module_id: str) -> Optional[float]:
        """Tempo desde a última transição pra READY, ou None se não READY."""
        entry = self._entries.get(module_id)
        if entry is None or entry.state != RuntimeState.READY:
            return None
        return (datetime.now(timezone.utc) - entry.since).total_seconds()


module_runtime_registry = ModuleRuntimeRegistry()
