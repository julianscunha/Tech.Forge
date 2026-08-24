"""
techforge start | stop | status — Phase 6
==========================================
Delegates to the Launcher package. The CLI is a thin wrapper; all logic
lives in launcher/techforge_launcher/.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

_LAUNCHER_DIR = Path(__file__).resolve().parent.parent.parent.parent / "launcher"
_PY = sys.executable


def _run_launcher(*args: str) -> int:
    result = subprocess.run(
        [_PY, "-m", "techforge_launcher", *args],
        cwd=str(_LAUNCHER_DIR),
    )
    return result.returncode


@click.command(name="start")
@click.option("--no-splash", is_flag=True, help="Disable the console startup screen.")
def start_cmd(no_splash: bool) -> None:
    """Start the complete TechForge platform (backend + frontend + browser)."""
    args = ["start"]
    if no_splash:
        args.append("--no-splash")
    raise SystemExit(_run_launcher(*args))


@click.command(name="stop")
def stop_cmd() -> None:
    """Stop the running TechForge platform (frontend → backend, no orphans)."""
    raise SystemExit(_run_launcher("stop"))


@click.command(name="status")
def status_cmd() -> None:
    """Show the current state of every TechForge component."""
    raise SystemExit(_run_launcher("status"))
