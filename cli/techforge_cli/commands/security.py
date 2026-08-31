"""techforge security status — Fase 17 §44/§45.

Cliente HTTP fino sobre /api/v1/security/status — nenhuma lógica de
trust duplicada aqui (mesmo padrão de commands/diagnostics.py).
Requer a plataforma rodando (`techforge start`).
"""
from __future__ import annotations

import json

import click

from techforge_cli.console import console, print_error, print_header

_CORE = "http://127.0.0.1:8000/api/v1"


def _get(path: str):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{_CORE}{path}", timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge start'.")
        raise SystemExit(1)


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
