"""techforge storage — Persistence health CLI (Fase 12 §30).

Consome a API do Core (/api/v1/system/storage/status) — nenhuma lógica de
health duplicada aqui.
"""
from __future__ import annotations

import click

from techforge_cli.console import console, print_error, print_info
from techforge_cli.http import core_get as _get


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
