"""techforge catalog — module catalog management commands.

Slice 5: list, search, show, sources (API calls to /catalog/*)
Slice 2: build-index (generate index.json + .mod files)
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path

import click
from rich.table import Table

from techforge_cli.console import (
    console,
    print_error,
    print_header,
    print_info,
    print_muted,
    print_section,
    print_success,
)
from techforge_cli.http import core_get as _get
from techforge_cli.packager.builder import PackageBuilder

# Add core backend to path for imports
ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))


@click.group("catalog")
def catalog_cmd():
    """Module catalog management."""
    pass


@catalog_cmd.command("list")
@click.option(
    "--category",
    default=None,
    help="Filter by category",
)
@click.option(
    "--source",
    default=None,
    help="Filter by source (local, official_catalog, custom_catalog)",
)
@click.option(
    "--page",
    type=int,
    default=1,
    help="Page number (default 1)",
)
@click.option(
    "--page-size",
    type=int,
    default=24,
    help="Items per page (default 24)",
)
def list_cmd(category, source, page, page_size):
    """List modules from the catalog."""
    params = []
    if category:
        params.append(f"category={urllib.parse.quote(category)}")
    if source:
        params.append(f"source={urllib.parse.quote(source)}")
    params.append(f"page={page}")
    params.append(f"page_size={page_size}")

    query_str = "&".join(params)
    path = f"/catalog/modules?{query_str}" if params else "/catalog/modules"

    data = _get(path)
    modules = data.get("items", [])

    if not modules:
        print_info("No modules found.")
        return

    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Category")
    table.add_column("Version")
    table.add_column("Source")
    table.add_column("Trust", style="yellow")
    table.add_column("Installed", style="green")

    for mod in modules:
        installed = "✓" if mod.get("is_installed") else ""
        table.add_row(
            mod["module_id"],
            mod.get("name", ""),
            mod.get("category", ""),
            mod.get("version", ""),
            mod.get("source", ""),
            mod.get("trust_level", ""),
            installed,
        )

    console.print(table)
    total = data.get("total", len(modules))
    print_muted(f"\nTotal: {total} • Page {page} of {(total + page_size - 1) // page_size}")


@catalog_cmd.command("search")
@click.argument("term")
def search_cmd(term):
    """Search for modules by name or description."""
    data = _get(f"/catalog/modules?search={urllib.parse.quote(term)}")
    modules = data.get("items", [])

    if not modules:
        print_info(f"No modules found matching '{term}'.")
        return

    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Category")
    table.add_column("Version")
    table.add_column("Source")

    for mod in modules:
        table.add_row(
            mod["module_id"],
            mod.get("name", ""),
            mod.get("category", ""),
            mod.get("version", ""),
            mod.get("source", ""),
        )

    console.print(table)


@catalog_cmd.command("show")
@click.argument("module_id")
def show_cmd(module_id):
    """Show detailed information about a module."""
    data = _get(f"/catalog/modules/{urllib.parse.quote(module_id)}")

    console.print(f"[cyan]{data['module_id']}[/cyan]  {data.get('name', '')}")
    print_muted(f"Version:       {data.get('version', '')}")
    print_muted(f"Category:      {data.get('category', '')}")
    print_muted(f"Author:        {data.get('author', '')}")
    print_muted(f"Publisher:     {data.get('publisher', '')}")
    print_muted(f"Source:        {data.get('source', '')}")
    print_muted(f"Trust Level:   {data.get('trust_level', '')}")
    print_muted(f"Installed:     {'Yes' if data.get('is_installed') else 'No'}")
    console.print()
    console.print(data.get("description", "(no description)"))


@catalog_cmd.command("sources")
def sources_cmd():
    """List configured catalog sources and their status."""
    sources = _get("/catalog/sources")

    if not sources:
        print_info("No sources configured.")
        return

    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Status", style="yellow")

    for src in sources:
        status_style = "green" if src.get("status") == "available" else "red"
        table.add_row(
            src["id"],
            src.get("name", ""),
            src.get("type", ""),
            f"[{status_style}]{src.get('status', '')}[/{status_style}]",
        )

    console.print(table)


@catalog_cmd.command("build-index")
@click.argument(
    "modules_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True),
    required=True,
    help="Output directory for index.json and .mod files",
)
def build_index_cmd(modules_dir, output):
    """
    Generate index.json and .mod files from a modules directory.

    Scans <modules_dir> for module subdirectories, packages each into
    a .mod file, and generates an index.json with metadata.

    \b
    Output:
        index.json              Module catalog (official format)
        <module_id>-<version>.mod   Packaged modules
        <module_id>-<version>.mod.sha256   Checksums

    \b
    Example:
        techforge catalog build-index ./modules --output ./dist/
    """
    modules_path = Path(modules_dir).resolve()
    output_path = Path(output).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    print_header(f"Build Module Catalog: {modules_path.name}")

    # ── Discover modules ────────────────────────────────────────────────────────

    modules_to_build = []
    for mod_dir in sorted(modules_path.iterdir()):
        if not mod_dir.is_dir():
            continue

        manifest_file = mod_dir / "manifest.yaml"
        if not manifest_file.exists():
            print_muted(f"  Skipping {mod_dir.name}: no manifest.yaml")
            continue

        modules_to_build.append(mod_dir)

    if not modules_to_build:
        print_error("No modules found (each must have manifest.yaml)")
        console.print()
        raise click.exceptions.Exit(1)

    print_info(f"Found {len(modules_to_build)} module(s) to package.")
    console.print()

    # ── Build .mod files ───────────────────────────────────────────────────────

    index_entries = []

    for mod_dir in modules_to_build:
        try:
            # Nested per-module output (<output>/<id>/<id>-<version>.mod) —
            # not flat — so every version ever built for a module stays on
            # disk next to its siblings. A new PR/version never overwrites
            # or orphans a previous one; the catalog keeps full history.
            module_output_dir = output_path / mod_dir.name
            module_output_dir.mkdir(parents=True, exist_ok=True)
            result = PackageBuilder.build(module_path=mod_dir, output_dir=module_output_dir)
            print_success(f"Packaged: {result.module_id}-{result.version}.mod")

            # Read the original manifest to include all metadata
            manifest_file = mod_dir / "manifest.yaml"
            import yaml

            manifest_data = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}

            # Build index entry
            entry = {
                "id": result.module_id,
                "name": manifest_data.get("name", result.module_id),
                "version": result.version,
                "category": manifest_data.get("category", "Uncategorized"),
                "vendor": manifest_data.get("vendor", ""),
                "author": manifest_data.get("author", ""),
                "description": manifest_data.get("description", ""),
                "mod_url": f"{result.module_id}/{result.module_id}-{result.version}.mod",
                "checksum": result.checksum,
            }
            index_entries.append(entry)

        except Exception as exc:
            print_error(f"Failed to package {mod_dir.name}: {exc}")
            raise click.exceptions.Exit(1)

    console.print()

    # ── Write index.json ───────────────────────────────────────────────────────

    print_info("Writing catalog index…")

    # Merge with whatever index.json already exists at --output, keyed by
    # id — never overwrite wholesale. A single run only ever sees the
    # modules currently present in the *source* dir (e.g. Tech.Forge.Modules'
    # submissions/, which only holds what's in-flight for one PR/merge);
    # blindly replacing index.json would silently drop every
    # previously-published module not part of this run.
    index_file = output_path / "index.json"
    existing_entries: dict[str, dict] = {}
    if index_file.exists():
        try:
            existing_data = json.loads(index_file.read_text(encoding="utf-8"))
            existing_entries = {m["id"]: m for m in existing_data.get("modules", [])}
        except (json.JSONDecodeError, KeyError):
            print_muted(f"  Ignoring unreadable existing {index_file.name}")

    for entry in index_entries:
        existing_entries[entry["id"]] = entry

    index_data = {"modules": sorted(existing_entries.values(), key=lambda m: m["id"])}
    index_file.write_text(
        json.dumps(index_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print_section("Catalog Complete")
    print_muted(f"Built this run: {len(index_entries)}")
    print_muted(f"Total in catalog: {len(index_data['modules'])}")
    print_muted(f"Location:  {output_path}")
    print_success(f"Index:     {index_file.name}")
    console.print()
    print_info("Ready for distribution (commit both .mod files and index.json).")
    console.print()
