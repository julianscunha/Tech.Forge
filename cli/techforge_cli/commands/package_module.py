"""techforge package-module — builds a .mod archive from a module directory."""
from __future__ import annotations

from pathlib import Path

import click

from techforge_cli.console import (
    console,
    print_error,
    print_header,
    print_info,
    print_muted,
    print_section,
    print_success,
)
from techforge_cli.packager.builder import PackageBuilder
from techforge_cli.validators.module_validator import ModuleCLIValidator


@click.command("package-module")
@click.argument("module_path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", default=None,
              help="Output directory for the .mod file (default: current directory)")
@click.option("--skip-validation", is_flag=True,
              help="Skip pre-packaging validation (not recommended)")
@click.option("--platform-version", default="1.0.0", show_default=True,
              help="Platform version for compatibility validation")
def package_module_cmd(module_path, output, skip_validation, platform_version):
    """
    Package a module directory into a distributable .mod file.

    The .mod format is a structured ZIP archive containing the module
    source, manifest, and build metadata. It is designed to be
    extended with digital signatures in Phase 5.

    \b
    Output: <module_id>-<version>.mod
            <module_id>-<version>.mod.sha256

    \b
    Examples:
        techforge package-module
        techforge package-module modules/installed/hello_world
        techforge package-module . --output dist/
    """
    path = Path(module_path).resolve()
    print_header(f"Package Module: {path.name}")

    # ── Pre-packaging validation ──────────────────────────────────────────────
    if not skip_validation:
        print_info("Running validation…")
        report = ModuleCLIValidator.validate(path, platform_version)
        if not report.passed:
            print_error("Validation failed — cannot package an invalid module.")
            console.print("  Run [accent]techforge validate-module[/accent] for the full report.")
            raise click.exceptions.Exit(1)
        print_success(f"Validation passed ({len(report.checks)} checks).")
    else:
        print_info("[warning]Skipping validation (--skip-validation)[/warning]")

    # ── Build ─────────────────────────────────────────────────────────────────
    output_dir = Path(output).resolve() if output else Path.cwd()
    console.print()
    print_info(f"Building archive in [path]{output_dir}[/path]…")

    try:
        result = PackageBuilder.build(module_path=path, output_dir=output_dir)
    except Exception as exc:
        print_error(f"Build failed: {exc}")
        raise click.exceptions.Exit(1)

    # ── Result ────────────────────────────────────────────────────────────────
    print_section("Build result")
    print_muted(f"Module:    {result.module_id}")
    print_muted(f"Version:   {result.version}")
    print_muted(f"Files:     {result.file_count}")
    print_muted(f"Size:      {result.size_human}")
    print_muted(f"Checksum:  {result.checksum[:16]}…  (SHA-256)")

    console.print()
    print_success(f"Package created: [path]{result.output_path}[/path]")
    print_info("Sidecar: [path]" + str(result.output_path) + ".sha256[/path]")

    console.print()
    print_info("To install, copy the module directory to:")
    print_muted("  <techforge_root>/modules/installed/<module_id>/")
    print_muted("  and restart the TechForge backend.")
    console.print()
