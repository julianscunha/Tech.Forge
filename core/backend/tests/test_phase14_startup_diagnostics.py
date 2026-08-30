"""
TechForge Fase 14 Slice 14 — Startup diagnostics
===================================================
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.observability.startup_diagnostics import StartupDiagnostics, time_step

pytestmark = pytest.mark.unit


class TestStartupDiagnostics:

    def test_record_step_stores_duration(self):
        diag = StartupDiagnostics()
        diag.record_step("database_init", 0.123456789)
        assert diag.steps["database_init"] == 0.123457

    def test_total_seconds_sums_all_steps(self):
        diag = StartupDiagnostics()
        diag.record_step("a", 1.0)
        diag.record_step("b", 2.5)
        assert diag.total_seconds == 3.5

    def test_snapshot_shape(self):
        diag = StartupDiagnostics()
        diag.record_step("a", 1.0)
        assert diag.snapshot() == {"steps": {"a": 1.0}, "total_seconds": 1.0}


class TestTimeStep:

    def test_time_step_records_into_module_singleton(self, monkeypatch):
        import app.observability.startup_diagnostics as mod
        fresh = StartupDiagnostics()
        monkeypatch.setattr(mod, "startup_diagnostics", fresh)

        with time_step("some_step"):
            pass

        assert "some_step" in fresh.steps
        assert fresh.steps["some_step"] >= 0

    def test_time_step_records_even_on_exception(self, monkeypatch):
        import app.observability.startup_diagnostics as mod
        fresh = StartupDiagnostics()
        monkeypatch.setattr(mod, "startup_diagnostics", fresh)

        with pytest.raises(ValueError):
            with time_step("failing_step"):
                raise ValueError("boom")

        assert "failing_step" in fresh.steps


@pytest.mark.integration
class TestRealStartupIsInstrumented:

    def test_lifespan_populates_expected_steps(self):
        from fastapi.testclient import TestClient

        from app.main import app
        from app.observability.startup_diagnostics import startup_diagnostics

        with TestClient(app):
            pass

        expected = {
            "database_init", "history_cleanup", "module_loader_scan",
            "plugin_loader_mount", "doc_indexer", "registry_sync_and_integrity",
            "service_registry_sync", "runtime_state_rebuild",
        }
        assert expected.issubset(startup_diagnostics.steps.keys())
        assert startup_diagnostics.total_seconds > 0
