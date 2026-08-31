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

pytestmark = pytest.mark.unit

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
        # already_running() reflete o backend (processo persistente), não
        # launcher_pid (a CLI de `start` sai assim que termina, por design).
        L._write_state({"backend_pid": os.getpid()})
        assert L.already_running() is True

    def test_stale_pid_reported_dead(self, clean_state):
        # PID 4 billion cannot exist on Windows or POSIX
        L._write_state({"backend_pid": 4_000_000_000})
        assert L.already_running() is False

    def test_corrupt_state_is_not_running(self, clean_state):
        clean_state.joinpath("state.json").write_text("{broken", encoding="utf-8")
        assert L.already_running() is False

    def test_start_focuses_existing_instance_static_mode(self, clean_state, monkeypatch):
        # Fase 16 §6 — "Focus existing application": reabre a URL em vez
        # de só reportar "já em execução".
        L._write_state({"backend_pid": os.getpid(), "frontend_mode": "static"})
        opened = {}
        monkeypatch.setattr(L.webbrowser, "open", lambda url: opened.setdefault("url", url))
        ok, msg = L.start(splash=False)
        assert ok is True
        assert opened["url"] == L.BACKEND_URL

    def test_start_focuses_existing_instance_dev_mode(self, clean_state, monkeypatch):
        L._write_state({"backend_pid": os.getpid(), "frontend_mode": "dev"})
        opened = {}
        monkeypatch.setattr(L.webbrowser, "open", lambda url: opened.setdefault("url", url))
        ok, msg = L.start(splash=False)
        assert ok is True
        assert opened["url"] == L.FRONTEND_URL


# ── Safe Mode (Fase 16 §16/§18) ──────────────────────────────────────────────────

class TestSafeMode:
    def test_start_sets_safe_mode_env_for_backend_process(self, clean_state, monkeypatch):
        captured: dict = {}

        def fake_spawn(cmd, cwd, log_file, env=None):
            captured["env"] = env
            return 12345

        monkeypatch.setattr(L, "_spawn", fake_spawn)
        monkeypatch.setattr(L, "wait_backend", lambda: False)  # curto-circuita após capturar o env

        L.start(splash=False, safe_mode=True)

        assert captured["env"].get("TECHFORGE_SAFE_MODE") == "true"

    def test_start_without_safe_mode_does_not_set_env(self, clean_state, monkeypatch):
        captured: dict = {}

        def fake_spawn(cmd, cwd, log_file, env=None):
            captured["env"] = env
            return 12345

        monkeypatch.setattr(L, "_spawn", fake_spawn)
        monkeypatch.setattr(L, "wait_backend", lambda: False)

        L.start(splash=False, safe_mode=False)

        assert "TECHFORGE_SAFE_MODE" not in captured["env"]


# ── Port guard (regressão: start() ignorava processos órfãos na porta) ─────────

class TestPortGuard:
    def test_port_in_use_false_when_nothing_listening(self):
        assert L._port_in_use("127.0.0.1", 1) is False

    def test_port_in_use_true_when_socket_bound(self):
        import socket
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]
        try:
            assert L._port_in_use("127.0.0.1", port) is True
        finally:
            srv.close()

    def test_start_refuses_when_port_occupied_by_orphan(self, clean_state, monkeypatch):
        # already_running() diz "não" (sem pidfile), mas a porta já está
        # ocupada por um processo que o launcher não conhece — start() não
        # pode simplesmente subir um segundo backend por cima.
        monkeypatch.setattr(L, "_port_in_use", lambda host, port: True)
        ok, msg = L.start(splash=False)
        assert ok is False
        assert str(L.BACKEND_PORT) in msg


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
        monkeypatch.setattr(L, "READY_URL", "http://127.0.0.1:1/nope")
        assert L.wait_backend(timeout=2) is False

    def test_http_ok_false_on_connection_error(self):
        assert L._http_ok("http://127.0.0.1:1/", timeout=0.5) is False


# ── Startup failure messages (Fase 16 §35) ──────────────────────────────────────

class TestStartupFailureMessage:
    def test_includes_diagnostic_code_and_no_stack_trace(self):
        msg = L._startup_failure_message("startup_backend", "Não foi possível iniciar o Backend.")
        assert "TF-STARTUP-001" in msg
        assert "Traceback" not in msg
        assert "Não foi possível iniciar o Backend." in msg

    def test_unknown_source_falls_back_to_generic_code(self):
        msg = L._startup_failure_message("something_made_up", "Falhou.")
        assert "TF-STARTUP-000" in msg


# ── Status (§15) ───────────────────────────────────────────────────────────────

class TestStatus:
    def test_status_all_stopped_when_no_state(self, clean_state, monkeypatch):
        # Determinístico independente do que estiver rodando de verdade na
        # máquina — sem isso, um backend real na porta configurada faz o
        # teste falhar (ver TestPortGuard, que cobre o caso ocupado).
        monkeypatch.setattr(L, "_port_in_use", lambda host, port: False)
        ps = L.status()
        summary = ps.summary()
        assert summary["launcher"]["state"] == "STOPPED"
        assert summary["backend"]["state"] == "STOPPED"
        assert summary["frontend"]["state"] == "STOPPED"

    def test_summary_shape_matches_spec(self, clean_state):
        keys = set(L.status().summary().keys())
        assert {"launcher", "backend", "frontend", "database", "runtime"} == keys

    def test_backend_not_reported_stopped_when_orphan_holds_port(self, clean_state, monkeypatch):
        """Regressão: sem pidfile (stale/limpo) mas com um processo órfão
        ainda ouvindo a porta, status() mentia 'STOPPED' — o usuário via
        tudo parado no `techforge status` enquanto múltiplos processos
        disputavam a porta e o SQLite por trás."""
        monkeypatch.setattr(L, "_port_in_use", lambda host, port: True)
        summary = L.status().summary()
        assert summary["backend"]["state"] != "STOPPED"

    def test_launcher_reported_ready_after_start_cli_process_exits(self, clean_state, monkeypatch):
        """Regressão: `techforge start` roda em foreground, sobe o backend,
        e SAI (devolve o prompt) assim que a plataforma fica pronta — por
        design, não é um daemon. `launcher_pid` gravado no state.json é o
        PID desse processo já morto; usar ele pra decidir "está rodando?"
        sempre reportava STOPPED mesmo com o backend saudável."""
        import subprocess
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            L._write_state({
                "launcher_pid": 4_000_000_000,  # processo do `start` já saiu
                "backend_pid": proc.pid,        # backend continua vivo
            })
            monkeypatch.setattr(L, "_http_ok", lambda url, timeout=2.0: True)
            assert L.already_running() is True
            assert L.status().launcher.state == "READY"
        finally:
            proc.kill()
            proc.wait()

    def test_frontend_reported_ready_in_desktop_static_mode(self, clean_state, monkeypatch):
        """Regressão: no modo Desktop não existe processo de frontend
        separado (o próprio backend serve dist/, frontend_pid=None) — mas
        `status()` reportava Frontend como STOPPED mesmo com o painel web
        acessível de verdade via backend."""
        import subprocess
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            L._write_state({
                "backend_pid": proc.pid,
                "frontend_pid": None,
                "frontend_mode": "static",
            })
            monkeypatch.setattr(L, "_http_ok", lambda url, timeout=2.0: True)
            assert L.status().frontend.state == "READY"
        finally:
            proc.kill()
            proc.wait()


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
