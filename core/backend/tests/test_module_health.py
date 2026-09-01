"""Regression tests for the public module health endpoint."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.api.routes import health
from app.module_engine.enums import ModuleStatus
from app.module_runtime.state import RuntimeState, module_runtime_registry


def _entry(status: ModuleStatus = ModuleStatus.INSTALLED):
    return SimpleNamespace(
        module_id="health_demo",
        name="Health Demo",
        status=status,
        entry_backend="backend/main.py",
        errors=[],
    )


def test_module_health_runs_runtime_hook_for_installed_module(monkeypatch):
    entry = _entry()
    monkeypatch.setattr(health.registry, "get", lambda module_id: entry)

    async def healthy_hook(module_id: str, entry_backend: str):
        assert (module_id, entry_backend) == ("health_demo", "backend/main.py")
        return module_runtime_registry.set_state(module_id, RuntimeState.READY).state

    monkeypatch.setattr("app.module_runtime.lifecycle.health_check", healthy_hook)

    result = asyncio.run(health.get_module_health("health_demo"))

    assert result.is_healthy
    assert result.issues == []


def test_module_health_reports_runtime_hook_failure(monkeypatch):
    entry = _entry()
    monkeypatch.setattr(health.registry, "get", lambda module_id: entry)

    async def failing_hook(module_id: str, entry_backend: str):
        return module_runtime_registry.set_state(
            module_id, RuntimeState.DEGRADED, last_error="dependency unavailable"
        ).state

    monkeypatch.setattr("app.module_runtime.lifecycle.health_check", failing_hook)

    result = asyncio.run(health.get_module_health("health_demo"))

    assert not result.is_healthy
    assert result.issues == ["dependency unavailable"]


def test_module_health_marks_timed_out_hook_as_unhealthy(monkeypatch):
    entry = _entry()
    monkeypatch.setattr(health.registry, "get", lambda module_id: entry)
    monkeypatch.setattr(health.settings, "MODULE_HEALTH_CHECK_TIMEOUT", 0.001)

    async def slow_hook(module_id: str, entry_backend: str):
        await asyncio.sleep(1)

    monkeypatch.setattr("app.module_runtime.lifecycle.health_check", slow_hook)

    result = asyncio.run(health.get_module_health("health_demo"))

    assert not result.is_healthy
    assert result.issues == ["health_check timed out after 0.001s"]


def test_module_health_does_not_run_hook_for_disabled_module(monkeypatch):
    entry = _entry(ModuleStatus.DISABLED)
    monkeypatch.setattr(health.registry, "get", lambda module_id: entry)

    async def unexpected_hook(module_id: str, entry_backend: str):
        raise AssertionError("health hook must not run for disabled modules")

    monkeypatch.setattr("app.module_runtime.lifecycle.health_check", unexpected_hook)

    result = asyncio.run(health.get_module_health("health_demo"))

    assert not result.is_healthy
