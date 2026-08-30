"""MetricEmitter — Fase 14 §10/§11.

Counter/Gauge/Histogram/Timer em memória, sem I/O, sem dependência nova.
"Não medir tudo" (spec) — só as métricas explicitamente listadas no §10
são instrumentadas (ver slice seguinte); este módulo é só a interface.
"""
from __future__ import annotations

import time
from collections import deque
from contextlib import contextmanager
from typing import Iterator

_HISTOGRAM_MAX_SAMPLES = 1000  # bounded (spec §37) — janela recente, não histórico completo


class Counter:
    def __init__(self) -> None:
        self._value = 0

    def inc(self, amount: int = 1) -> None:
        self._value += amount

    @property
    def value(self) -> int:
        return self._value


class Gauge:
    def __init__(self) -> None:
        self._value: float = 0.0

    def set(self, value: float) -> None:
        self._value = value

    def inc(self, amount: float = 1) -> None:
        self._value += amount

    def dec(self, amount: float = 1) -> None:
        self._value -= amount

    @property
    def value(self) -> float:
        return self._value


class Histogram:
    def __init__(self) -> None:
        self._samples: deque[float] = deque(maxlen=_HISTOGRAM_MAX_SAMPLES)
        self._count = 0
        self._sum = 0.0

    def observe(self, value: float) -> None:
        self._samples.append(value)
        self._count += 1
        self._sum += value

    def snapshot(self) -> dict[str, float]:
        if not self._samples:
            return {"count": 0, "sum": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0}
        return {
            "count": self._count,   # total histórico, não limitado à janela
            "sum": round(self._sum, 6),
            "min": round(min(self._samples), 6),
            "max": round(max(self._samples), 6),
            "avg": round(sum(self._samples) / len(self._samples), 6),
        }


class Timer:
    """Context manager: mede a duração do bloco e registra num Histogram."""

    def __init__(self, histogram: Histogram) -> None:
        self._histogram = histogram
        self._start = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.monotonic()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._histogram.observe(time.monotonic() - self._start)


class MetricEmitter:
    def __init__(self) -> None:
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}

    def counter(self, name: str) -> Counter:
        return self._counters.setdefault(name, Counter())

    def gauge(self, name: str) -> Gauge:
        return self._gauges.setdefault(name, Gauge())

    def histogram(self, name: str) -> Histogram:
        return self._histograms.setdefault(name, Histogram())

    @contextmanager
    def timer(self, name: str) -> Iterator[Timer]:
        with Timer(self.histogram(name)) as t:
            yield t

    def snapshot(self) -> dict[str, dict]:
        return {
            "counters": {k: v.value for k, v in self._counters.items()},
            "gauges": {k: v.value for k, v in self._gauges.items()},
            "histograms": {k: v.snapshot() for k, v in self._histograms.items()},
        }


metric_emitter = MetricEmitter()
