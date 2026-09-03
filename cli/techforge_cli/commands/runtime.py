"""techforge runtime — Module Runtime CLI (Fase 9 §27).

Consome a API do Core (/api/v1/runtime*) — nenhuma lógica de discovery/
execução duplicada aqui.
"""
from __future__ import annotations

import click
from rich.table import Table

from techforge_cli.console import console, print_info
from techforge_cli.http import core_get as _get
from techforge_cli.http import core_post as _post


@click.group("runtime")
def runtime_cmd():
    """Inspect the Module Runtime (per-module Runtime State)."""


@runtime_cmd.command("status")
def status_cmd():
    """Platform-wide runtime status (Fase 6 foundation)."""
    data = _get("/runtime/status")
    for key, value in data.items():
        console.print(f"  {key}: {value}")


@runtime_cmd.command("modules")
def modules_cmd():
    """List Runtime State of every INSTALLED module."""
    entries = _get("/runtime/modules")
    if not entries:
        print_info("Nenhum módulo com Runtime State (nenhum INSTALLED).")
        return
    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("Module ID", style="cyan")
    table.add_column("State")
    table.add_column("Uptime (s)")
    table.add_column("Last error")
    for e in entries:
        table.add_row(e["module_id"], e["state"],
                      f"{e['uptime_seconds']:.1f}" if e.get("uptime_seconds") is not None else "-",
                      e.get("last_error") or "-")
    console.print(table)


@runtime_cmd.command("module")
@click.argument("module_id")
def module_cmd(module_id):
    """Show Runtime State of one module."""
    e = _get(f"/runtime/modules/{module_id}")
    console.print(f"[cyan]{e['module_id']}[/cyan]")
    console.print(f"  State:          {e['state']}")
    console.print(f"  Uptime (s):     {e.get('uptime_seconds')}")
    console.print(f"  Last error:     {e.get('last_error') or '(none)'}")
    console.print(f"  Last execution: {e.get('last_execution') or '(none)'}")


@runtime_cmd.command("initialize")
@click.argument("module_id")
def initialize_cmd(module_id):
    """Re-run health_check() on demand for a module."""
    e = _post(f"/runtime/modules/{module_id}/initialize")
    console.print(f"[cyan]{e['module_id']}[/cyan] → {e['state']}")
