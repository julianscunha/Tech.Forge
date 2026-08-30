"""techforge config — Platform configuration export (Fase 12 §16/§30).

Consome a API do Core (/api/v1/config) — nenhuma lógica duplicada aqui.
"""
from __future__ import annotations

import json

import click

from techforge_cli.console import console, print_error

_CORE = "http://127.0.0.1:8000/api/v1"


def _get(path: str):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{_CORE}{path}", timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge platform start'.")
        raise SystemExit(1)


@click.group("config")
def config_cmd():
    """Platform configuration (Fase 12)."""


@config_cmd.command("export")
def export_cmd():
    """Print the platform's effective configuration as JSON."""
    data = _get("/config")
    console.print(json.dumps(data, indent=2, ensure_ascii=False))
