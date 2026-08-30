"""techforge docs — Documentation Engine CLI (Fase 5 §20).

Consome a API do Core (/api/v1/docs/*) — nenhuma lógica de indexação/busca
duplicada aqui.
"""
from __future__ import annotations

import json

import click
from rich.table import Table

from techforge_cli.console import (
    console,
    print_error,
    print_info,
)

_CORE = "http://127.0.0.1:8000/api/v1"


def _get(path: str, raw: bool = False):
    """GET na API do Core. Levanta SystemExit com mensagem amigável em erro."""
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{_CORE}{path}", timeout=15) as resp:
            data = resp.read()
            return data.decode("utf-8") if raw else json.loads(data)
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge platform start'.")
        raise SystemExit(1)


@click.group("docs")
def docs_cmd():
    """Search and export TechForge documentation (Documentation Engine)."""


@docs_cmd.command("list")
def list_cmd():
    """List all indexed documents."""
    docs = _get("/docs/list")
    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("Doc ID", style="cyan")
    table.add_column("Title")
    table.add_column("Category")
    for d in docs:
        table.add_row(d.get("doc_id", ""), d.get("title", ""), d.get("category", ""))
    console.print(table)
    print_info(f"{len(docs)} documento(s).")


@docs_cmd.command("search")
@click.argument("query")
def search_cmd(query):
    """Search documentation by query."""
    results = _get(f"/docs/search?q={query}")
    if not results:
        print_info(f"Nenhum resultado para '{query}'.")
        return
    for r in results:
        title = r.get("title", "")
        doc_id = r.get("doc_id", "")
        snippet = (r.get("snippet") or "")[:100]
        console.print(f"[cyan]{doc_id}[/cyan]  {title}")
        if snippet:
            console.print(f"  [dim]{snippet}…[/dim]")


@docs_cmd.command("get")
@click.argument("path")
def get_cmd(path):
    """Print one article's content by path."""
    article = _get(f"/docs/article/{path}")
    console.print(article.get("content", ""))


@docs_cmd.command("export-context")
@click.option("--scope", default=None, help="Filter categories (e.g. module-development)")
def export_context_cmd(scope):
    """Export AI context from the Documentation Engine."""
    path = "/docs/export/ai-context"
    if scope:
        path += f"?categories={scope}"
    text = _get(path, raw=True)
    console.print(text)
