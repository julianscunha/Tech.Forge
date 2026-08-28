"""techforge catalog — module catalog management commands."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from techforge_cli.console import (
    console,
    print_header,
    print_success,
    print_error,
    print_info,
    print_section,
    print_muted,
)
from techforge_cli.packager.builder import PackageBuilder

# Add core backend to path for imports
ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))


@click.command("build-index")
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
            result = PackageBuilder.build(module_path=mod_dir, output_dir=output_path)
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
                "mod_url": f"{result.module_id}-{result.version}.mod",
                "checksum": result.checksum,
            }
            index_entries.append(entry)

        except Exception as exc:
            print_error(f"Failed to package {mod_dir.name}: {exc}")
            raise click.exceptions.Exit(1)

    console.print()

    # ── Write index.json ───────────────────────────────────────────────────────

    print_info("Writing catalog index…")
    index_data = {"modules": sorted(index_entries, key=lambda m: m["id"])}
    index_file = output_path / "index.json"
    index_file.write_text(
        json.dumps(index_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print_section("Catalog Complete")
    print_muted(f"Modules:   {len(index_entries)}")
    print_muted(f"Location:  {output_path}")
    print_success(f"Index:     {index_file.name}")
    console.print()
    print_info("Ready for distribution (commit both .mod files and index.json).")
    console.print()
