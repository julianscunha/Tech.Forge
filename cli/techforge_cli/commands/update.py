"""
techforge update — Self-update do Core via git pull.
======================================================
Único mecanismo de update suportado hoje — a plataforma ainda é
distribuída como repositório + build manual (sem instalador GUI/MSI,
ver docs/limitations.md). Só funciona em checkout git.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click
from rich.markdown import Markdown

from techforge_cli.commands.platform import _run_launcher
from techforge_cli.console import console, print_error, print_info, print_section, print_warning

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PY = sys.executable


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(_REPO_ROOT), capture_output=True, text=True
    )


@click.command(name="update")
@click.option("--yes", "-y", is_flag=True, help="Não perguntar confirmação.")
def update_cmd(yes: bool) -> None:
    """Atualiza o Core (git pull + deps + build + migrations) para a última release publicada."""
    if not (_REPO_ROOT / ".git").is_dir():
        print_error("Não é um checkout git — update automático só funciona em clone de desenvolvimento.")
        raise SystemExit(1)

    status = _git("status", "--porcelain")
    if status.stdout.strip():
        print_error("Há mudanças não commitadas no repositório. Commit ou stash antes de atualizar.")
        raise SystemExit(1)

    sys.path.insert(0, str(_REPO_ROOT / "core" / "backend"))
    import asyncio

    from app.core.settings import settings
    from app.services.update_check import check_for_update

    result = asyncio.run(check_for_update())
    if not result.update_available:
        print_info(f"Já está na última versão ({settings.PLATFORM_VERSION}).")
        return

    console.print(f"Nova versão disponível: {settings.PLATFORM_VERSION} → {result.latest_version}")
    if result.release_notes:
        print_section(f"Release notes — v{result.latest_version}")
        console.print(Markdown(result.release_notes))

    print_warning("Isso vai parar a plataforma (se estiver rodando) durante o update e reiniciá-la ao final.")
    if not yes and not click.confirm("Atualizar agora?", default=True):
        raise SystemExit(0)

    print_info("Parando a plataforma...")
    _run_launcher("stop")

    print_info("git pull origin main...")
    pull = _git("pull", "origin", "main")
    if pull.returncode != 0:
        print_error(f"git pull falhou:\n{pull.stderr}")
        raise SystemExit(1)

    print_info("Atualizando dependências do backend...")
    pip = subprocess.run(
        [_PY, "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=str(_REPO_ROOT / "core" / "backend"),
    )
    if pip.returncode != 0:
        print_error("pip install falhou — o repositório já foi atualizado (git pull); "
                     "rode manualmente 'pip install -r core/backend/requirements.txt'.")
        raise SystemExit(1)

    print_info("Rodando migrations...")
    from app.db import migrations as db_migrations
    db_migrations.upgrade_head()

    print_info("Buildando o frontend (npm run build)...")
    npm = subprocess.run(["npm", "run", "build"], cwd=str(_REPO_ROOT / "core" / "frontend"))
    if npm.returncode != 0:
        print_error("Build do frontend falhou — corrija manualmente e rode "
                     "'cd core/frontend && npm run build' antes de iniciar a plataforma.")
        raise SystemExit(1)

    print_info(f"Atualizado para {result.latest_version}. Iniciando a plataforma...")
    raise SystemExit(_run_launcher("start"))
