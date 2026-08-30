"""techforge version — Platform version CLI (Fase 15 §24).

Acesso direto a `app.core.settings` (não via HTTP) — mesmo racional do
`techforge migrations status`: precisa funcionar mesmo com a plataforma
parada. O frontend consome `GET /api/v1/system/version` em vez disso.
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

from techforge_cli.console import console

_CORE_BACKEND = Path(__file__).resolve().parents[3] / "core" / "backend"
if str(_CORE_BACKEND) not in sys.path:
    sys.path.insert(0, str(_CORE_BACKEND))


@click.command("version")
def version_cmd():
    """Show the running TechForge Core version."""
    from app.core.settings import settings

    console.print(f"TechForge {settings.PLATFORM_VERSION}")
