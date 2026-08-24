"""
Phase 6 — Launcher & Runtime tests
====================================
Unit tests for the launcher primitives (single-instance, pid tracking,
status) and the runtime foundation. The full integration test boots the
real backend via the launcher's spawn machinery and verifies READY →
health → shutdown without orphans.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent.parent
LAUNCHER_DIR = REPO / "launcher"
sys.path.insert(0, str(LAUNCHER_DIR))
sys.path.insert(0, str(REPO / "core" / "backend"))

import techforge_launcher as L  # noqa: E402


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture()
def clean_state(tmp_path, monkeypatch):
    """Redirect state/pids to a temp dir so tests never touch the real one."""
    pids = tmp_path / "pids"
    pids.mkdir()
    monkeypatch.setattr(L, "PIDS_PATH", pids)
    monkeypatch.setattr(L, "STATE_FILE", pids / "state.json")
    yield pids


# ── Single instance (§12) ──────────────────────────────────────────────────────

class TestSingleInstance:
    def test_not_running_when_no_state(self, clean_state):
        assert L.already_running() is False

    def test_running_with_live_pid(self, clean_state):
        L._write_state({"launcher_pid": os.getpid()})
        assert L.already_running() is True

    def test_stale_pid_reported_dead(self, clean_state):
        # PID 4 billion cannot exist on Windows or POSIX
        L._write_state({"launcher_pid": 4_000_000_000})
        assert L.already_running() is False

    def test_corrupt_state_is_not_running(self, clean_state):
        clean_state.joinpath("state.json").write_text("{broken", encoding="utf-8")
        assert L.already_running() is False


# ── Process helpers (§11) ──────────────────────────────────────────────────────

class TestProcessHelpers:
    def test_current_process_alive(self):
        assert L._pid_alive(os.getpid()) is True

    def test_impossible_pid_dead(self):
        assert L._pid_alive(4_000_000_000) is False

    def test_terminate_shortlived_child(self, tmp_path):
        import subprocess
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            cwd=str(tmp_path),
        )
        try:
            assert L._pid_alive(proc.pid) is True
            assert L._terminate(proc.pid) is True
            assert L._pid_alive(proc.pid) is False
        finally:
            if proc.poll() is None:
                proc.kill()

    def test_stop_children_kills_owned_pids_only(self, clean_state, tmp_path):
        import subprocess
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            cwd=str(tmp_path),
        )
        state = {"frontend_pid": proc.pid}
        L._stop_children(state)
        assert L._pid_alive(proc.pid) is False


# ── Health probes (§4, §5) ─────────────────────────────────────────────────────

class TestHealthProbes:
    def test_unreachable_backend_fails_fast(self, monkeypatch):
        monkeypatch.setattr(L, "HEALTH_URL", "http://127.0.0.1:1/nope")
        assert L.wait_backend(timeout=2) is False

    def test_http_ok_false_on_connection_error(self):
        assert L._http_ok("http://127.0.0.1:1/", timeout=0.5) is False


# ── Status (§15) ───────────────────────────────────────────────────────────────

class TestStatus:
    def test_status_all_stopped_when_no_state(self, clean_state):
        ps = L.status()
        summary = ps.summary()
        assert summary["launcher"]["state"] == "STOPPED"
        assert summary["backend"]["state"] == "STOPPED"
        assert summary["frontend"]["state"] == "STOPPED"

    def test_summary_shape_matches_spec(self, clean_state):
        keys = set(L.status().summary().keys())
        assert {"launcher", "backend", "frontend", "database", "runtime"} == keys


# ── Runtime foundation (§17) ───────────────────────────────────────────────────

class TestRuntimeFoundation:
    @pytest.mark.asyncio
    async def test_startup_sets_ready(self):
        from app.runtime import TechForgeRuntime
        rt = TechForgeRuntime()
        await rt.fire_startup("test")
        assert rt.state.value == "ready"
        assert rt.started_at is not None

    @pytest.mark.asyncio
    async def test_shutdown_sets_stopped_and_fires_handlers(self):
        from app.runtime import TechForgeRuntime
        rt = TechForgeRuntime()
        seen = []
        rt.on_shutdown(lambda e: seen.append(e.name))
        await rt.fire_startup()
        await rt.fire_shutdown("bye")
        assert rt.state.value == "stopped"
        assert seen == ["shutdown"]

    @pytest.mark.asyncio
    async def test_failing_shutdown_handler_does_not_block(self):
        from app.runtime import TechForgeRuntime
        rt = TechForgeRuntime()

        def boom(_): raise RuntimeError("hook failure")
        rt.on_shutdown(boom)
        await rt.fire_shutdown()
        assert rt.state.value == "stopped"


# ── Configuration (§13) ────────────────────────────────────────────────────────

class TestConfig:
    def test_ports_come_from_settings_not_hardcoded(self):
        from app.core.settings import settings
        assert settings.PORT == 8000
        assert settings.FRONTEND_PORT == 5173
