"""techforge docs — Documentation Engine CLI (Fase 5 §20).

Consome a API do Core (/api/v1/docs/*) — nenhuma lógica de indexação/busca
duplicada aqui.
"""
from __future__ import annotations

import click
from rich.table import Table

from techforge_cli.console import (
    console,
    print_info,
)
from techforge_cli.http import core_get as _get


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
