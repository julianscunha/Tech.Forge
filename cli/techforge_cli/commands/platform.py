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


def _log_path(source: str) -> Path:
    """Caminho do arquivo de log do launcher (fonte única de paths)."""
    # derive repo root: launcher/../logs
    repo_root = _LAUNCHER_DIR.parent
    return repo_root / "logs" / f"{source}.log"


@click.command(name="logs")
@click.option("--backend", "source", flag_value="backend", help="Log do backend.")
@click.option("--frontend", "source", flag_value="frontend", help="Log do frontend.")
@click.option("--launcher", "source", flag_value="launcher", help="Log do launcher.")
@click.option("-n", "--lines", default=50, show_default=True, help="Últimas N linhas.")
@click.option("-f", "--follow", is_flag=True, help="Acompanhar o log ao vivo (Fase 14 §35, techforge logs tail).")
def logs_cmd(source: str | None, lines: int, follow: bool) -> None:
    """Mostrar as últimas linhas dos logs da plataforma (§16)."""
    if not source:
        raise click.UsageError("Escolha uma origem: --backend, --frontend ou --launcher.")
    path = _log_path(source)
    if not path.is_file():
        click.echo(f"Nenhum log encontrado em {path}. A plataforma já foi executada?")
        raise SystemExit(1)
    content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in content[-lines:]:
        click.echo(line)

    if follow:
        _follow_file(path)


def _follow_file(path: Path) -> None:
    """Poll simples (sem dependência nova) — imprime linhas novas conforme
    são gravadas, até Ctrl+C."""
    import time

    with path.open("r", encoding="utf-8", errors="replace") as f:
        f.seek(0, 2)  # fim do arquivo — só o que vier depois
        try:
            while True:
                line = f.readline()
                if line:
                    click.echo(line.rstrip("\n"))
                else:
                    time.sleep(0.5)
        except KeyboardInterrupt:
            pass


@click.command(name="dev")
@click.pass_context
def dev_cmd(ctx: click.Context) -> None:
    """Modo desenvolvimento: backend com reload + frontend dev server (§17)."""
    raise SystemExit(_run_launcher("start", "--dev"))
