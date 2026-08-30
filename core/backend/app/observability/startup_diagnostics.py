"""Startup diagnostics — Fase 14 §16.

Duração de cada etapa do lifespan, pra diagnosticar startup lento sem
precisar instrumentar manualmente toda vez. Estado do boot mais recente
apenas — não é histórico (não faz sentido reter starts antigos, o processo
só tem um boot ativo por vez).
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator


class StartupDiagnostics:
    def __init__(self) -> None:
        self.steps: dict[str, float] = {}

    def record_step(self, name: str, duration_seconds: float) -> None:
        self.steps[name] = round(duration_seconds, 6)

    @property
    def total_seconds(self) -> float:
        return round(sum(self.steps.values()), 6)

    def snapshot(self) -> dict[str, object]:
        return {"steps": dict(self.steps), "total_seconds": self.total_seconds}


startup_diagnostics = StartupDiagnostics()


@contextmanager
def time_step(name: str) -> Iterator[None]:
    start = time.monotonic()
    try:
        yield
    finally:
        startup_diagnostics.record_step(name, time.monotonic() - start)
