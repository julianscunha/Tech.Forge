"""
TechForge Fase 14 Slice 7 — Métricas iniciais instrumentadas
===============================================================
Wiring de metric_emitter nos pontos reais do código (spec §10): não
testa o MetricEmitter em si (já coberto no slice 6), testa que os
eventos certos incrementam a métrica certa.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.observability.metrics import metric_emitter

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _fresh_metrics():
    """Cada teste vê contadores zerados — metric_emitter é singleton global."""
    metric_emitter._counters.clear()
    metric_emitter._gauges.clear()
    metric_emitter._histograms.clear()
    yield


class TestPlatformStartups:

    def test_fire_startup_increments_counter(self):
        from app.runtime import TechForgeRuntime
        asyncio.run(TechForgeRuntime().fire_startup("test"))
        assert metric_emitter.counter("platform_startups").value == 1


class TestRuntimeErrors:

    def test_degraded_transition_increments_counter(self):
        from app.runtime import TechForgeRuntime, RuntimeState
        rt = TechForgeRuntime()
        rt.state = RuntimeState.READY
        rt.register_component_pid("fake", 999_999_999)  # PID que não existe
        rt.check_liveness()
        assert metric_emitter.counter("runtime_errors").value == 1


class TestModuleLoads:

    def test_store_increments_by_installed_count(self):
        from app.module_engine import journal as loader_journal
        from app.module_engine.loader import LoaderResult
        loader_journal.store(LoaderResult(installed=3))
        assert metric_emitter.counter("module_loads").value == 3

    def test_store_with_zero_installed_does_not_increment(self):
        from app.module_engine import journal as loader_journal
        from app.module_engine.loader import LoaderResult
        loader_journal.store(LoaderResult(installed=0))
        assert metric_emitter.counter("module_loads").value == 0


class TestDependencyFailures:

    def test_failed_required_check_increments_counter(self):
        from app.dependency_engine.validator import DependencyValidator
        # dependência malformada -> DependencyParseError -> check required=False? checa abaixo
        DependencyValidator.validate("application", [{"target": {}}])
        assert metric_emitter.counter("dependency_failures").value >= 1

    def test_no_failures_does_not_increment(self):
        from app.dependency_engine.validator import DependencyValidator
        DependencyValidator.validate("application", [])
        assert metric_emitter.counter("dependency_failures").value == 0


class TestModuleExecutions:

    def test_successful_invoke_increments_executions_and_duration(self, monkeypatch):
        from app.service_registry import invoker
        from app.service_registry.descriptor import ServiceStatus

        class FakeExport:
            name = "ping"
            parameters = []

        class FakeContract:
            exports = [FakeExport()]

        class FakeDescriptor:
            module_id = "hello_world"
            status = ServiceStatus.ACTIVE
            contract = FakeContract()

        monkeypatch.setattr(invoker.service_registry, "find_service", lambda sid: FakeDescriptor())
        monkeypatch.setattr(invoker, "_load_export_callable", lambda mid, name: lambda: "pong")

        result = invoker.invoke("hello_world", "ping")

        assert result == "pong"
        assert metric_emitter.counter("module_executions").value == 1
        assert metric_emitter.histogram("execution_duration").snapshot()["count"] == 1
        assert metric_emitter.counter("execution_failures").value == 0

    def test_failed_invoke_increments_failures(self, monkeypatch):
        from app.service_registry import invoker
        from app.service_registry.descriptor import ServiceStatus
        from app.service_registry.errors import ServiceExecutionFailedError

        class FakeExport:
            name = "boom"
            parameters = []

        class FakeContract:
            exports = [FakeExport()]

        class FakeDescriptor:
            module_id = "hello_world"
            status = ServiceStatus.ACTIVE
            contract = FakeContract()

        def _raise():
            raise ValueError("boom")

        monkeypatch.setattr(invoker.service_registry, "find_service", lambda sid: FakeDescriptor())
        monkeypatch.setattr(invoker, "_load_export_callable", lambda mid, name: _raise)

        with pytest.raises(ServiceExecutionFailedError):
            invoker.invoke("hello_world", "boom")

        assert metric_emitter.counter("module_executions").value == 1
        assert metric_emitter.counter("execution_failures").value == 1
