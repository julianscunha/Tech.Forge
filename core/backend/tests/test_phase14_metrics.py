"""
TechForge Fase 14 Slice 6 — MetricEmitter
============================================
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.observability.metrics import Histogram, MetricEmitter

pytestmark = pytest.mark.unit


class TestCounter:

    def test_starts_at_zero(self):
        assert MetricEmitter().counter("x").value == 0

    def test_inc_default_is_one(self):
        c = MetricEmitter().counter("x")
        c.inc()
        assert c.value == 1

    def test_inc_by_amount(self):
        c = MetricEmitter().counter("x")
        c.inc(5)
        assert c.value == 5

    def test_same_name_returns_same_instance(self):
        emitter = MetricEmitter()
        assert emitter.counter("x") is emitter.counter("x")


class TestGauge:

    def test_set_and_read(self):
        g = MetricEmitter().gauge("x")
        g.set(42)
        assert g.value == 42

    def test_inc_dec(self):
        g = MetricEmitter().gauge("x")
        g.set(10)
        g.inc(5)
        g.dec(3)
        assert g.value == 12


class TestHistogram:

    def test_empty_snapshot(self):
        assert Histogram().snapshot() == {"count": 0, "sum": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0}

    def test_observe_and_snapshot(self):
        h = Histogram()
        h.observe(1.0)
        h.observe(3.0)
        h.observe(2.0)
        snap = h.snapshot()
        assert snap["count"] == 3
        assert snap["min"] == 1.0
        assert snap["max"] == 3.0
        assert snap["avg"] == 2.0

    def test_bounded_sample_window_does_not_grow_unbounded(self):
        h = Histogram()
        for i in range(2000):
            h.observe(float(i))
        # count total continua exato mesmo com janela de amostras limitada
        assert h.snapshot()["count"] == 2000
        assert len(h._samples) <= 1000


class TestTimer:

    def test_records_duration_into_histogram(self):
        emitter = MetricEmitter()
        with emitter.timer("op"):
            time.sleep(0.01)
        snap = emitter.histogram("op").snapshot()
        assert snap["count"] == 1
        assert snap["min"] > 0


class TestMetricEmitterSnapshot:

    def test_snapshot_shape(self):
        emitter = MetricEmitter()
        emitter.counter("c").inc()
        emitter.gauge("g").set(5)
        emitter.histogram("h").observe(1.0)
        snap = emitter.snapshot()
        assert snap == {
            "counters": {"c": 1},
            "gauges": {"g": 5},
            "histograms": {"h": {"count": 1, "sum": 1.0, "min": 1.0, "max": 1.0, "avg": 1.0}},
        }
