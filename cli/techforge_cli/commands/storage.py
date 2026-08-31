"""techforge storage — Persistence health CLI (Fase 12 §30).

Consome a API do Core (/api/v1/system/storage/status) — nenhuma lógica de
health duplicada aqui.
"""
from __future__ import annotations

import json

import click

from techforge_cli.console import console, print_error, print_info

from techforge_cli.config import CORE_BASE_URL as _CORE


def _get(path: str):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{_CORE}{path}", timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge platform start'.")
        raise SystemExit(1)


@click.group("storage")
def storage_cmd():
    """Storage & persistence health (Fase 12)."""


@storage_cmd.command("status")
def status_cmd():
    """Show database availability and writability."""
    health = _get("/system/storage/status")
    if health.get("database") and health.get("writable"):
        print_info("Data Store: Healthy")
    else:
        print_error("Data Store: Unhealthy")
    console.print(f"  Database: {'ok' if health.get('database') else 'error'}")
    console.print(f"  Writable: {'ok' if health.get('writable') else 'error'}")
