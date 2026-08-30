"""
TechForge Launcher (Phase 6)
============================
Bootstrap orchestrator: starts Backend, waits for health, starts Frontend,
opens the browser, monitors processes, and shuts everything down in order.

Rules (spec §2, §18):
  - no business logic
  - does not load modules
  - reuses existing settings/logging — no duplication
  - identifies ONLY the processes it started (never kills generic python/node)
  - single-instance guard via pidfile with liveness check

Platform abstraction (§16): process spawn/termination is delegated to a
ProcessManager; Windows and POSIX implementations share the same interface.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path

# Reuse backend settings as the single source of configuration truth (§13)
_LAUNCHER_PKG_DIR = Path(__file__).resolve().parent          # launcher/techforge_launcher
REPO_ROOT = _LAUNCHER_PKG_DIR.parent.parent                  # repo root
sys.path.insert(0, str(REPO_ROOT / "core" / "backend"))
try:
    from app.core.settings import settings  # type: ignore
    BASE_DIR = settings.BASE_DIR
    BACKEND_HOST = settings.HOST
    BACKEND_PORT = settings.PORT
    FRONTEND_PORT = settings.FRONTEND_PORT
    HEALTH_TIMEOUT = settings.HEALTH_CHECK_TIMEOUT
    FRONTEND_TIMEOUT = settings.FRONTEND_READY_TIMEOUT
except Exception:  # pragma: no cover — fallback if backend deps are missing
    BASE_DIR = REPO_ROOT
    BACKEND_HOST = "127.0.0.1"
    BACKEND_PORT = 8000
    FRONTEND_PORT = 5173
    HEALTH_TIMEOUT = 60
    FRONTEND_TIMEOUT = 60

# Paths are always derived from the repo layout, never from CWD
LOGS_PATH = REPO_ROOT / "logs"
PIDS_PATH = LOGS_PATH / "pids"
LAUNCHER_LOG = LOGS_PATH / "launcher.log"
BACKEND_DIR = REPO_ROOT / "core" / "backend"
FRONTEND_DIR = REPO_ROOT / "core" / "frontend"

BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
FRONTEND_URL = f"http://{BACKEND_HOST}:{FRONTEND_PORT}"
FRONTEND_DIST = (REPO_ROOT / "core" / "frontend" / "dist")
HEALTH_URL = f"{BACKEND_URL}/api/v1/platform/status"
STATE_FILE = PIDS_PATH / "state.json"

logger = logging.getLogger("techforge.launcher")


# ── Logging setup (launcher-specific file; core keeps its own) ────────────────

def _setup_logging() -> None:
    LOGS_PATH.mkdir(parents=True, exist_ok=True)
    if not logger.handlers:
        handler = logging.FileHandler(LAUNCHER_LOG, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


# ── Data types ─────────────────────────────────────────────────────────────────

@dataclass
class ComponentStatus:
    name: str
    state: str                      # READY | STOPPED | FAILING | UNKNOWN
    detail: str = ""


@dataclass
class PlatformState:
    launcher: ComponentStatus = field(default_factory=lambda: ComponentStatus("Launcher", "STOPPED"))
    backend:  ComponentStatus = field(default_factory=lambda: ComponentStatus("Backend", "STOPPED"))
    frontend: ComponentStatus = field(default_factory=lambda: ComponentStatus("Frontend", "STOPPED"))
    database: ComponentStatus = field(default_factory=lambda: ComponentStatus("Database", "UNKNOWN"))
    runtime:  ComponentStatus = field(default_factory=lambda: ComponentStatus("Runtime", "UNKNOWN"))

    def summary(self) -> dict:
        return {c.name.lower(): {"state": c.state, "detail": c.detail}
                for c in (self.launcher, self.backend, self.frontend,
                          self.database, self.runtime)}


# ── Process helpers ────────────────────────────────────────────────────────────

def _pid_alive(pid: int) -> bool:
    """Check whether a PID exists WITHOUT killing anything generic."""
    try:
        if sys.platform == "win32":
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, timeout=10,
            ).stdout.decode("utf-8", errors="ignore")
            return str(pid) in out
        else:
            os.kill(pid, 0)  # signal 0 = existence probe only
            return True
    except Exception:
        return False


def _win_child_pids(pid: int) -> list[int]:
    """All live descendant PIDs of `pid` on Windows (via tasklist CSV)."""
    try:
        out = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True, timeout=15,
        ).stdout.decode("utf-8", errors="ignore")
    except Exception:
        return []
    # rows: "name","pid","session","n","mem"
    rows = {}
    import csv as _csv
    import io
    for row in _csv.reader(io.StringIO(out)):
        if len(row) >= 3 and row[1].isdigit():
            rows[int(row[1])] = int(row[3]) if row[3].isdigit() else 0
    # BFS over parent→children (row[3] is PPID)
    children = {}
    for p, pp in rows.items():
        children.setdefault(pp, []).append(p)
    result, queue = [], [pid]
    while queue:
        current = queue.pop()
        for child in children.get(current, []):
            if child not in result:
                result.append(child)
                queue.append(child)
    return result


def _terminate(pid: int) -> bool:
    """
    Terminate a process we own AND all of its descendants.

    On Windows, npm.cmd spawns node → vite as a chain; killing only the top
    PID leaves the actual server orphaned. So on win32 we kill the deepest
    children first, then the process itself.
    """
    if not _pid_alive(pid):
        return True
    try:
        if sys.platform == "win32":
            tree = [p for p in _win_child_pids(pid) if _pid_alive(p)]
            for child in reversed(tree):   # leaves first
                subprocess.run(["taskkill", "/PID", str(child), "/F"],
                               capture_output=True, timeout=15)
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, timeout=15)
        else:
            import signal
            os.kill(pid, signal.SIGTERM)
            for _ in range(30):
                if _reap_if_child(pid) or not _pid_alive(pid):
                    return True
                time.sleep(0.2)
            os.kill(pid, signal.SIGKILL)
            _reap_if_child(pid)
    except Exception as exc:
        logger.warning("Failed to terminate PID %s: %s", pid, exc)
        return False
    return not _pid_alive(pid)


def _reap_if_child(pid: int) -> bool:
    """
    POSIX only: after SIGTERM/SIGKILL, a child becomes a zombie until its
    parent calls wait() — `os.kill(pid, 0)` still succeeds on a zombie, so
    `_pid_alive()` would wrongly report it as alive. Reap it if we are the
    parent (e.g. our own test/launcher spawned it via subprocess.Popen);
    no-op if we aren't (e.g. `techforge stop` invoked as a separate process
    targeting a PID from the state file) — nothing we can do about that
    zombie's reaping from outside anyway.

    Returns True if the process was confirmed gone (reaped or already
    reaped by someone else).
    """
    try:
        reaped_pid, _ = os.waitpid(pid, os.WNOHANG)
        return reaped_pid == pid
    except ChildProcessError:
        return False


def _spawn(cmd: list[str], cwd: Path, log_file: Path, env: dict | None = None) -> int:
    """Spawn a detached child whose output goes to its own log file."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    kwargs: dict = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    with open(log_file, "ab") as fh:
        proc = subprocess.Popen(
            cmd, cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT,
            env=env or os.environ.copy(), **kwargs
        )
    logger.info("Spawned %s (cwd=%s) → PID %s, log=%s", " ".join(cmd), cwd, proc.pid, log_file.name)
    return proc.pid


# ── Single-instance guard (§12) ────────────────────────────────────────────────

def _read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(state: dict) -> None:
    PIDS_PATH.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _clear_state() -> None:
    try:
        STATE_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def already_running() -> bool:
    """True when the platform is genuinely running.

    Checks the backend process — the actual persistent process — not
    `launcher_pid`: the CLI invocation that runs `start()` exits normally
    once startup completes (control returns to the shell), by design.
    Using `launcher_pid` here always reported "not running" right after
    a successful start, even with a perfectly healthy backend.
    """
    state = _read_state()
    pid = state.get("backend_pid")
    return bool(pid and _pid_alive(int(pid)))


# ── Health probes ──────────────────────────────────────────────────────────────

def _http_ok(url: str, timeout: float = 2.0) -> bool:
    """
    Probe a URL over HTTP. Tries the hostname as given, then the IPv6
    loopback equivalent — Vite's dev server binds to ::1 only by default.
    """
    candidates = [url]
    if url.startswith("http://127.0.0.1"):
        candidates.append(url.replace("http://127.0.0.1", "http://[::1]", 1))
    for candidate in candidates:
        try:
            with urllib.request.urlopen(candidate, timeout=timeout) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, socket.timeout, OSError):
            continue
    return False


def wait_backend(timeout: int = HEALTH_TIMEOUT) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _http_ok(HEALTH_URL):
            return True
        time.sleep(1.0)
    return False


def wait_frontend(timeout: int = FRONTEND_TIMEOUT) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _http_ok(FRONTEND_URL):
            return True
        time.sleep(1.0)
    return False


# ── Commands ───────────────────────────────────────────────────────────────────

def _python_exe() -> str:
    venv = BACKEND_DIR / ".venv" / ("Scripts" if sys.platform == "win32" else "bin")
    exe = venv / ("python.exe" if sys.platform == "win32" else "python")
    return str(exe) if exe.exists() else sys.executable


def _npm_exe() -> str:
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if npm:
        return npm
    raise FileNotFoundError("npm not found on PATH")


def start(splash: bool = True, dev_mode: bool = False) -> tuple[bool, str]:
    """
    Full startup sequence (§3). Returns (success, user_message).
    Technical details go to logs/launcher.log only (§6).

    dev_mode=True (§17): força backend com reload + vite dev server.
    Default (desktop): backend sem reload servindo dist/ quando existir;
    vite dev server apenas como fallback se não houver build.
    """
    _setup_logging()
    t0 = time.time()

    if already_running():
        logger.info("start requested but platform already running")
        return True, "TechForge já está em execução."

    from techforge_launcher.splash import Splash
    splash_ui = Splash(enabled=splash)

    state: dict = {"launcher_pid": os.getpid()}
    _write_state(state)   # persist immediately so a second `start` sees us (§12)
    try:
        # ── 1. Environment ─────────────────────────────────────────────────
        splash_ui.step("Ambiente")
        python_exe = _python_exe()

        # ── 2. Backend ─────────────────────────────────────────────────────
        splash_ui.step("Backend")
        desktop = (not dev_mode) and (FRONTEND_DIST / "index.html").is_file()
        env = dict(os.environ, SERVE_STATIC_FRONTEND="true") if desktop else dict(os.environ)
        backend_pid = _spawn(
            [python_exe, "-m", "uvicorn", "app.main:app",
             "--host", BACKEND_HOST, "--port", str(BACKEND_PORT)],
            cwd=BACKEND_DIR, log_file=LOGS_PATH / "backend.log", env=env,
        )
        state["backend_pid"] = backend_pid
        _write_state(state)

        if not wait_backend():
            msg = "TechForge não conseguiu iniciar o Backend."
            logger.error(msg + " (health check timeout after %ss)", HEALTH_TIMEOUT)
            _stop_children(state)
            _clear_state()
            splash_ui.fail(msg)
            return False, msg
        state["backend_ready"] = True

        # ── 3. Frontend ────────────────────────────────────────────────────
        state["frontend_mode"] = "dev" if not desktop else "static"

        if desktop:
            # §10 — backend serve o build estático; nenhum processo node.
            splash_ui.step("Interface (estática)")
            state["frontend_pid"] = None
            ui_url = BACKEND_URL
        else:
            splash_ui.step("Frontend")
            frontend_pid = _spawn([_npm_exe(), "run", "dev"], cwd=FRONTEND_DIR,
                                  log_file=LOGS_PATH / "frontend.log")
            state["frontend_pid"] = frontend_pid
            _write_state(state)

            if not wait_frontend():
                msg = "TechForge não conseguiu iniciar a interface."
                logger.error(msg + " (frontend not responding after %ss)", FRONTEND_TIMEOUT)
                _stop_children(state)
                _clear_state()
                splash_ui.fail(msg)
                return False, msg
            ui_url = FRONTEND_URL

        # ── 4. Browser ─────────────────────────────────────────────────────
        splash_ui.step("Plataforma")
        webbrowser.open(ui_url)

        elapsed = time.time() - t0
        state["ready_at"] = elapsed
        _write_state(state)
        logger.info("Startup complete in %.1fs — %s", elapsed, ui_url)
        splash_ui.done(elapsed)
        return True, f"TechForge operacional em {ui_url}"

    except Exception as exc:
        msg = "TechForge não conseguiu iniciar."
        logger.exception("Startup failed: %s", exc)
        _stop_children(state)
        _clear_state()
        splash_ui.fail(msg)
        return False, msg


def _stop_children(state: dict) -> None:
    """Shutdown order (§11): Frontend → Backend. Only PIDs we own."""
    for key in ("frontend_pid", "backend_pid"):
        pid = state.get(key)
        if pid:
            logger.info("Stopping %s=%s", key, pid)
            _terminate(int(pid))


def stop() -> tuple[bool, str]:
    """Coordinated shutdown of a running instance."""
    _setup_logging()
    state = _read_state()
    if not state:
        return True, "TechForge não está em execução."

    _stop_children(state)
    launcher_pid = state.get("launcher_pid")
    if launcher_pid and int(launcher_pid) != os.getpid():
        _terminate(int(launcher_pid))
    _clear_state()
    logger.info("Shutdown complete.")
    return True, "TechForge encerrado."


def status() -> PlatformState:
    """Live status of every component (§15)."""
    _setup_logging()
    ps = PlatformState()

    running = already_running()
    ps.launcher = ComponentStatus(
        "Launcher", "READY" if running else "STOPPED",
        detail=f"backend_pid={_read_state().get('backend_pid')}" if running else "",
    )

    state = _read_state()
    backend_pid = state.get("backend_pid")
    if backend_pid and _pid_alive(int(backend_pid)):
        healthy = _http_ok(HEALTH_URL)
        db_ok = _http_ok(f"{BACKEND_URL}/api/v1/health")
        rt_ok = _http_ok(f"{BACKEND_URL}/api/v1/runtime/status")
        ps.backend = ComponentStatus("Backend", "READY" if healthy else "FAILING")
        ps.database = ComponentStatus("Database", "READY" if db_ok else "FAILING")
        ps.runtime = ComponentStatus("Runtime", "READY" if rt_ok else "FAILING")
    else:
        ps.backend = ComponentStatus("Backend", "STOPPED")
        ps.database = ComponentStatus("Database", "STOPPED")
        ps.runtime = ComponentStatus("Runtime", "STOPPED")

    if state.get("frontend_mode") == "static":
        # Desktop: sem processo Node separado — a UI é servida pelo
        # próprio backend (dist/ estático), então o status do frontend
        # é o mesmo do backend, não "STOPPED" por falta de PID próprio.
        ps.frontend = ComponentStatus("Frontend", ps.backend.state, detail="estático via backend")
    else:
        frontend_pid = state.get("frontend_pid")
        if frontend_pid and _pid_alive(int(frontend_pid)):
            fe_ok = _http_ok(FRONTEND_URL)
            ps.frontend = ComponentStatus("Frontend", "READY" if fe_ok else "FAILING")
        else:
            ps.frontend = ComponentStatus("Frontend", "STOPPED")

    return ps
