"""
TechForge Fase 14 Slice 8 — execution_id + correlação básica
================================================================
service_registry.invoker.invoke() é o único ponto real de execução de
módulo hoje (ModuleExecutionContext ainda não é usado em produção) —
por isso a correlação de log é ligada ali: qualquer log emitido durante
a chamada carrega module_id/execution_id automaticamente via Log Context
(slice 1), sem o módulo precisar fazer nada.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.observability.context import get_log_context

pytestmark = pytest.mark.unit


class TestInvokeCorrelation:

    def test_module_id_and_execution_id_available_during_invoke(self, monkeypatch):
        from app.service_registry import invoker
        from app.service_registry.descriptor import ServiceStatus

        captured = {}

        def fake_func():
            captured.update(get_log_context())
            return "ok"

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
        monkeypatch.setattr(invoker, "_load_export_callable", lambda mid, name: fake_func)

        invoker.invoke("hello_world", "ping")

        assert captured["module_id"] == "hello_world"
        assert "execution_id" in captured
        assert captured["execution_id"]

    def test_context_restored_after_invoke(self, monkeypatch):
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
        monkeypatch.setattr(invoker, "_load_export_callable", lambda mid, name: (lambda: "ok"))

        invoker.invoke("hello_world", "ping")

        assert get_log_context() == {}

    def test_distinct_execution_id_per_invoke_call(self, monkeypatch):
        from app.service_registry import invoker
        from app.service_registry.descriptor import ServiceStatus

        seen = []

        def fake_func():
            seen.append(get_log_context()["execution_id"])
            return "ok"

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
        monkeypatch.setattr(invoker, "_load_export_callable", lambda mid, name: fake_func)

        invoker.invoke("hello_world", "ping")
        invoker.invoke("hello_world", "ping")

        assert seen[0] != seen[1]
