"""techforge security status — Fase 17 §44/§45.

Cliente HTTP fino sobre /api/v1/security/status — nenhuma lógica de
trust duplicada aqui (mesmo padrão de commands/diagnostics.py).
Requer a plataforma rodando (`techforge start`).
"""
from __future__ import annotations

import click

from techforge_cli.console import console, print_header
from techforge_cli.http import core_get as _get


@click.group("security", invoke_without_command=True)
@click.pass_context
def security_cmd(ctx: click.Context) -> None:
    """Security & Trust overview across installed modules (Fase 17)."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(security_status_cmd)


@security_cmd.command("status")
def security_status_cmd() -> None:
    """Show aggregate trust posture: modules by trust level, unsigned, revoked."""
    data = _get("/security/status")
    print_header("TechForge — Security Status")
    console.print(f"Total modules:      {data['total_modules']}")
    console.print(f"Unsigned modules:   {data['unsigned_count']}")
    console.print(f"Revoked publishers: {data['revoked_publishers']}")
    console.print("By trust level:")
    for level, count in data["by_trust_level"].items():
        console.print(f"  {level:<12} {count}")
