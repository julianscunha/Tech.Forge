"""techforge verify-module / integrity check / publishers list|show — Fase 10 §23/§24.

Consome a API do Core (/api/v1/modules/{id}/verify|integrity|trust,
/api/v1/publishers*) — nenhuma lógica de verificação duplicada aqui.

techforge sign-module / verify-signature NÃO implementados — dependem
de assinatura real (SignatureProvider é só abstração nesta fase).
"""
from __future__ import annotations

import json

import click
from rich.table import Table

from techforge_cli.console import console, print_error, print_info

_CORE = "http://127.0.0.1:8000/api/v1"


def _get(path: str):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{_CORE}{path}", timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print_error(exc.read().decode("utf-8", errors="replace"))
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge platform start'.")
        raise SystemExit(1)


def _post(path: str):
    import urllib.error
    import urllib.request
    req = urllib.request.Request(f"{_CORE}{path}", data=b"", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print_error(exc.read().decode("utf-8", errors="replace"))
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge platform start'.")
        raise SystemExit(1)


def _print_integrity_result(result: dict) -> None:
    console.print(f"[cyan]{result['module_id']}[/cyan] → {result['status']}")
    if result.get("modified_files"):
        console.print(f"  modified: {result['modified_files']}")
    if result.get("missing_files"):
        console.print(f"  missing: {result['missing_files']}")
    if result.get("unexpected_files"):
        console.print(f"  unexpected: {result['unexpected_files']}")


@click.command("verify-module")
@click.argument("module_id")
def verify_module_cmd(module_id):
    """Reverify an installed module's integrity on demand."""
    _print_integrity_result(_post(f"/modules/{module_id}/verify"))


@click.group("integrity")
def integrity_cmd():
    """Inspect module integrity manifests."""


@integrity_cmd.command("check")
@click.argument("module_id")
def integrity_check_cmd(module_id):
    """Show a module's current integrity status (read-only, no side effects)."""
    _print_integrity_result(_get(f"/modules/{module_id}/integrity"))


@click.group("publishers")
def publishers_cmd():
    """Inspect the Publisher Registry."""


@publishers_cmd.command("list")
def publishers_list_cmd():
    """List all known publishers."""
    publishers = _get("/publishers")
    if not publishers:
        print_info("Nenhum publisher registrado.")
        return
    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Trust Status")
    for p in publishers:
        table.add_row(p["id"], p["name"], p["type"], p["trust_status"])
    console.print(table)


@publishers_cmd.command("show")
@click.argument("publisher_id")
def publishers_show_cmd(publisher_id):
    """Show details of one publisher."""
    p = _get(f"/publishers/{publisher_id}")
    console.print(f"[cyan]{p['id']}[/cyan]  {p['name']}")
    console.print(f"  Type:         {p['type']}")
    console.print(f"  Trust Status: {p['trust_status']}")
    console.print(f"  Public key:   {p.get('public_key') or '(none)'}")
