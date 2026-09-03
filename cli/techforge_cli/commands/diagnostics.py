"""techforge diagnostics — health/errors/export (Fase 14 §35).

Cliente HTTP fino sobre /api/v1/diagnostics* — nenhuma lógica duplicada
aqui, mesmo padrão de `techforge_cli.http` usado no resto do CLI.
Requer a plataforma rodando (`techforge start`).
"""
from __future__ import annotations

from pathlib import Path

import click
from rich.table import Table

from techforge_cli.console import console, print_header, print_info, print_success
from techforge_cli.http import core_get as _core_get
from techforge_cli.http import core_post_raw as _core_post_raw


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


@diagnostics_cmd.command("security")
def diagnostics_security_cmd() -> None:
    """Show aggregate security posture (alias of `security status`, Fase 17)."""
    from techforge_cli.commands.security import security_status_cmd
    security_status_cmd.callback()


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
