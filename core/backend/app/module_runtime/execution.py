"""
ModuleExecutionResult + Cancellation/Progress — Fase 9 §16/§19/§21 Slice 5
==============================================================================
Envelope padronizado de execução e esqueleto de tipos pra cancelamento e
progresso. Decisão do usuário: sem fluxo real de longa duração pra
exercitar nesta fase — nenhum módulo hoje precisa disso de verdade.
Disponível para quando um módulo de execução longa existir (ex: coleta
AWS, health check VMware).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ── Resultado padronizado (§19) ────────────────────────────────────────────────

@dataclass
class ModuleExecutionResult:
    status:           str
    data:             Any = None
    warnings:         list[str] = field(default_factory=list)
    errors:           list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    metadata:         dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, data: Any = None, warnings: Optional[list[str]] = None,
                duration_seconds: float = 0.0, **metadata: Any) -> "ModuleExecutionResult":
        return cls(status="SUCCESS", data=data, warnings=warnings or [],
                   duration_seconds=duration_seconds, metadata=metadata)

    @classmethod
    def failure(cls, errors: list[str], duration_seconds: float = 0.0,
                **metadata: Any) -> "ModuleExecutionResult":
        return cls(status="FAILED", errors=errors, duration_seconds=duration_seconds,
                   metadata=metadata)


# ── Cancellation (§16) ──────────────────────────────────────────────────────────

class ExecutionCancelledError(Exception):
    """Levantada por CancellationToken.raise_if_cancelled() quando cancelado."""


class CancellationToken:
    """Sinalização cooperativa — o módulo decide quando checar, o Runtime
    nunca mata a execução à força (§16: 'não matar processos indiscriminadamente')."""

    def __init__(self) -> None:
        self._cancelled = False

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True

    def raise_if_cancelled(self) -> None:
        if self._cancelled:
            raise ExecutionCancelledError("execution was cancelled")


# ── Progress (§21) ───────────────────────────────────────────────────────────────

class ProgressPhase(str, Enum):
    PREPARING  = "PREPARING"
    RUNNING    = "RUNNING"
    FINALIZING = "FINALIZING"


@dataclass
class ProgressReport:
    phase:   ProgressPhase
    percent: Optional[int] = None

    def __post_init__(self) -> None:
        if self.percent is not None and not (0 <= self.percent <= 100):
            raise ValueError(f"percent must be between 0 and 100, got {self.percent}")
