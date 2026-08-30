"""
TechForge Fase 14 Slice 5 — EventBus unificado
=================================================
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.observability.events import Event, EventBus

pytestmark = pytest.mark.unit


class TestEventBus:

    def test_publish_notifies_subscribers(self):
        bus = EventBus()
        received = []
        bus.subscribe(received.append)
        bus.publish("runtime.startup", detail="backend started")
        assert len(received) == 1
        assert received[0].type == "runtime.startup"
        assert received[0].payload == {"detail": "backend started"}

    def test_multiple_subscribers_all_notified(self):
        bus = EventBus()
        a, b = [], []
        bus.subscribe(a.append)
        bus.subscribe(b.append)
        bus.publish("x")
        assert len(a) == 1
        assert len(b) == 1

    def test_unsubscribe_stops_notifications(self):
        bus = EventBus()
        received = []
        bus.subscribe(received.append)
        bus.unsubscribe(received.append)
        bus.publish("x")
        assert received == []

    def test_failing_subscriber_does_not_block_others(self):
        bus = EventBus()
        received = []

        def bad(event):
            raise ValueError("boom")

        bus.subscribe(bad)
        bus.subscribe(received.append)
        bus.publish("x")  # não deve levantar
        assert len(received) == 1

    def test_event_as_dict_includes_type_timestamp_and_payload(self):
        event = Event(type="module_loader.scan", payload={"installed": 3})
        d = event.as_dict()
        assert d["type"] == "module_loader.scan"
        assert d["installed"] == 3
        assert "timestamp" in d

    def test_publish_returns_the_event(self):
        bus = EventBus()
        event = bus.publish("x", foo="bar")
        assert event.type == "x"
        assert event.payload == {"foo": "bar"}


class TestEventBusMigration:
    """Sistemas existentes (RuntimeEvent, OperationLog, LoaderJournal)
    passam a publicar no EventBus além de manter seu próprio buffer —
    suas APIs de leitura continuam 100% inalteradas."""

    def test_runtime_publishes_startup_event(self):
        from app.observability.events import event_bus
        from app.runtime import TechForgeRuntime

        received = []
        event_bus.subscribe(received.append)
        try:
            rt = TechForgeRuntime()
            asyncio.run(rt.fire_startup("test detail"))
            startup_events = [e for e in received if e.type == "runtime.startup"]
            assert len(startup_events) == 1
            assert startup_events[0].payload["detail"] == "test detail"
            # API de leitura existente continua igual
            assert rt.events[-1].name == "startup"
        finally:
            event_bus.unsubscribe(received.append)

    def test_operation_log_publishes_event(self):
        from app.observability.events import event_bus
        from app.package_manager.operation_log import OperationLog

        received = []
        event_bus.subscribe(received.append)
        try:
            log = OperationLog()
            log.record("install", "hello_world", "1.0.0", "success", "installed ok")
            pkg_events = [e for e in received if e.type == "package_manager.install"]
            assert len(pkg_events) == 1
            assert pkg_events[0].payload["module_id"] == "hello_world"
            assert pkg_events[0].payload["status"] == "success"
            # API de leitura existente continua igual
            assert log.all()[0].module_id == "hello_world"
        finally:
            event_bus.unsubscribe(received.append)

    def test_loader_journal_publishes_event_on_store(self):
        from app.module_engine import journal as loader_journal
        from app.module_engine.loader import LoaderResult
        from app.observability.events import event_bus

        received = []
        event_bus.subscribe(received.append)
        try:
            result = LoaderResult()
            loader_journal.store(result)
            scan_events = [e for e in received if e.type == "module_loader.scan"]
            assert len(scan_events) == 1
            # API de leitura existente continua igual
            assert loader_journal.get() is result
        finally:
            event_bus.unsubscribe(received.append)
