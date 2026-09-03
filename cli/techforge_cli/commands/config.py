"""techforge config — Platform configuration export (Fase 12 §16/§30).

Consome a API do Core (/api/v1/config) — nenhuma lógica duplicada aqui.
"""
from __future__ import annotations

import json

import click

from techforge_cli.console import console
from techforge_cli.http import core_get as _get


@click.group("config")
def config_cmd():
    """Platform configuration (Fase 12)."""


@config_cmd.command("export")
def export_cmd():
    """Print the platform's effective configuration as JSON."""
    data = _get("/config")
    console.print(json.dumps(data, indent=2, ensure_ascii=False))
