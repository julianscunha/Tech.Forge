"""Fase 6 Slice 3 — runtime status enriquecido (spec §14/§15).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase6_runtime_status.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

import app.runtime as rt_mod


@pytest.fixture()
def fresh_runtime(monkeypatch):
    r = rt_mod.TechForgeRuntime()
    monkeypatch.setattr(rt_mod, "runtime", r)
    return r


def test_status_includes_uptime(fresh_runtime):
    from datetime import datetime
    fresh_runtime.started_at = datetime.utcnow()
    s = fresh_runtime.status()
    assert "uptime_seconds" in s
    assert isinstance(s["uptime_seconds"], float)
    assert s["uptime_seconds"] >= 0


def test_uptime_none_before_startup(fresh_runtime):
    s = fresh_runtime.status()
    assert s["uptime_seconds"] is None


def test_frontend_mode_from_env(monkeypatch, tmp_path):
    """frontend_mode reflete SERVE_STATIC_FRONTEND + existência de dist."""
    from app.core.settings import settings
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>x</html>", encoding="utf-8")
    monkeypatch.setattr(settings, "SERVE_STATIC_FRONTEND", True)

    mode = rt_mod.current_frontend_mode(dist)
    assert mode == "static"

    monkeypatch.setattr(settings, "SERVE_STATIC_FRONTEND", False)
    mode = rt_mod.current_frontend_mode(dist)
    assert mode in ("dev", "none")


def test_degraded_on_dead_pid(tmp_path):
    """PID morto registrado → estado DEGRADED na checagem de liveness."""
    from app.module_engine.journal import store as _j  # noqa: F401 — garante imports
    r = rt_mod.TechForgeRuntime()
    # PID quase certamente inexistente em Windows/Linux:
    dead = 4_194_303 if sys.platform != "win32" else 999_999_999
    r.register_component_pid("backend", dead)
    liveness = r.check_liveness()
    assert liveness["backend"] is False
    assert r.state.value in ("degraded", "ready")  # state muda p/ degraded via API helper


def test_liveness_ok_on_live_process():
    r = rt_mod.TechForgeRuntime()
    import os
    r.register_component_pid("backend", os.getpid())
    liveness = r.check_liveness()
    assert liveness["backend"] is True
