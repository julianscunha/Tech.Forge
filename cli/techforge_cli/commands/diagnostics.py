"""techforge diagnostics — health/errors/export (Fase 14 §35).

Cliente HTTP fino sobre /api/v1/diagnostics* — nenhuma lógica duplicada
aqui, mesmo padrão de `_core_get` já usado em commands/modules.py.
Requer a plataforma rodando (`techforge start`).
"""
from __future__ import annotations

import json
from pathlib import Path

import click
from rich.table import Table

from techforge_cli.console import console, print_error, print_header, print_info, print_success

_BASE = "http://127.0.0.1:8000/api/v1"


def _core_get(path: str):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{_BASE}{path}", timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge start'.")
        raise SystemExit(1)


def _core_post_raw(path: str) -> bytes:
    import urllib.error
    import urllib.request
    req = urllib.request.Request(f"{_BASE}{path}", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge start'.")
        raise SystemExit(1)


@click.group("diagnostics", invoke_without_command=True)
@click.pass_context
def diagnostics_cmd(ctx: click.Context) -> None:
    """System diagnostics — health, errors, executions, export (Fase 14)."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(diagnostics_health_cmd)


@diagnostics_cmd.command("health")
def diagnostics_health_cmd() -> None:
    """Show platform + storage + runtime health."""
    data = _core_get("/diagnostics/health")
    print_header("TechForge — Diagnostics")
    console.print(f"Platform: {data['platform']['name']} v{data['platform']['version']}")
    console.print(f"Database: {data['platform']['database_status']}")
    console.print(f"Storage writable: {data['storage']['writable']}")
    console.print(f"Runtime state: {data['runtime']['state']}")
    console.print(
        f"Modules installed: {data['platform']['modules_installed']} "
        f"(enabled: {data['platform']['modules_enabled']})"
    )


@diagnostics_cmd.command("errors")
@click.option("-n", "--limit", default=20, show_default=True, help="Quantidade máxima de erros.")
def diagnostics_errors_cmd(limit: int) -> None:
    """Show recent errors from the Error Registry."""
    errors = _core_get(f"/diagnostics/errors?limit={limit}")
    if not errors:
        print_info("Nenhum erro registrado.")
        return
    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("Code")
    table.add_column("Module")
    table.add_column("Message")
    table.add_column("When")
    for e in errors:
        table.add_row(e.get("code") or e["source"], e.get("module_id") or "-",
                     e["message"], e.get("created_at") or "-")
    console.print(table)


@diagnostics_cmd.command("export")
@click.option("--format", "fmt", type=click.Choice(["json", "txt", "zip"]), default="json",
             show_default=True, help="Formato do export.")
@click.option("-o", "--output", type=click.Path(), default=None, help="Caminho de saída.")
def diagnostics_export_cmd(fmt: str, output: str | None) -> None:
    """Export a Diagnostic Report (json/txt) or Support Bundle (zip)."""
    content = _core_post_raw(f"/diagnostics/export?format={fmt}")
    path = Path(output) if output else Path(f"techforge-diagnostics.{fmt}")
    if fmt == "zip":
        path.write_bytes(content)
    else:
        path.write_text(content.decode("utf-8"), encoding="utf-8")
    print_success(f"Exportado para {path}")
