"""techforge services — Service Registry CLI (Fase 8 §24).

Consome a API do Core (/api/v1/services*) — nenhuma lógica de discovery/
invocação duplicada aqui.
"""
from __future__ import annotations

import json

import click
from rich.table import Table

from techforge_cli.console import console, print_error, print_info

_CORE = "http://127.0.0.1:8000/api/v1"


def _get(path: str):
    """GET na API do Core. Levanta SystemExit com mensagem amigável em erro."""
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{_CORE}{path}", timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge platform start'.")
        raise SystemExit(1)


@click.group("services")
def services_cmd():
    """Discover and inspect Service Modules (Service Registry)."""


@services_cmd.command("list")
def list_cmd():
    """List all registered services."""
    services = _get("/services")
    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("Service ID", style="cyan")
    table.add_column("Module")
    table.add_column("Status")
    table.add_column("Capabilities")
    for s in services:
        table.add_row(s.get("service_id", ""), s.get("module_id", ""),
                      s.get("status", ""), ", ".join(s.get("capabilities", [])))
    console.print(table)
    print_info(f"{len(services)} serviço(s).")


@services_cmd.command("show")
@click.argument("service_id")
def show_cmd(service_id):
    """Show one service descriptor."""
    s = _get(f"/services/{service_id}")
    console.print(f"[cyan]{s.get('service_id')}[/cyan]  ({s.get('module_id')})")
    console.print(f"  Status:       {s.get('status')}")
    console.print(f"  Module ver.:  {s.get('module_version')}")
    console.print(f"  Service ver.: {s.get('service_version')}")
    console.print(f"  Capabilities: {', '.join(s.get('capabilities', [])) or '(none)'}")


@services_cmd.command("search")
@click.argument("query")
def search_cmd(query):
    """Search services by keyword (service_id, capabilities, export name/description)."""
    import urllib.parse
    services = _get(f"/services?q={urllib.parse.quote(query)}")
    if not services:
        print_info(f"Nenhum serviço encontrado para '{query}'.")
        return
    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("Service ID", style="cyan")
    table.add_column("Module")
    table.add_column("Status")
    table.add_column("Capabilities")
    for s in services:
        table.add_row(s.get("service_id", ""), s.get("module_id", ""),
                      s.get("status", ""), ", ".join(s.get("capabilities", [])))
    console.print(table)


@services_cmd.command("capabilities")
def capabilities_cmd():
    """List every discovered capability and its provider(s)."""
    caps = _get("/services/capabilities")
    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("Capability", style="cyan")
    table.add_column("Provided by")
    for cap, providers in caps.items():
        table.add_row(cap, ", ".join(providers))
    console.print(table)


@services_cmd.command("contract")
@click.argument("service_id")
def contract_cmd(service_id):
    """Show a service's public contract (exports)."""
    contract = _get(f"/services/{service_id}/contract")
    console.print(f"[cyan]{contract.get('service_id')}[/cyan] v{contract.get('version')}")
    console.print(contract.get("description", ""))
    for exp in contract.get("exports", []):
        console.print(f"\n  [bold]{exp.get('name')}[/bold] — {exp.get('description')}")
        console.print(f"    returns: {exp.get('returns')}")


@services_cmd.command("status")
def status_cmd():
    """Summarize service availability (active / unavailable / failed)."""
    services = _get("/services")
    by_status: dict[str, int] = {}
    for s in services:
        by_status[s.get("status", "")] = by_status.get(s.get("status", ""), 0) + 1
    for status, count in sorted(by_status.items()):
        console.print(f"  {status}: {count}")
    print_info(f"{len(services)} serviço(s) no total.")
