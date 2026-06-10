"""techforge validate-module — full module validation with detailed report."""
from __future__ import annotations

from pathlib import Path
import click
from rich.table import Table

from techforge_cli.console import (
    console, print_header, print_success, print_error,
    print_warning, print_info, print_section, print_muted,
)
from techforge_cli.validators.module_validator import ModuleCLIValidator


@click.command("validate-module")
@click.argument("module_path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--platform-version", default="1.0.0", show_default=True,
              help="Platform version to check compatibility against")
@click.option("--strict", is_flag=True,
              help="Treat warnings as errors (non-zero exit on any warning)")
def validate_module_cmd(module_path, platform_version, strict):
    """
    Validate a module directory and print a detailed report.

    MODULE_PATH defaults to the current directory.

    \b
    Checks performed:
      · manifest.yaml exists and is valid YAML
      · All required fields are present
      · Module id is valid snake_case
      · Version strings follow semver (X.Y.Z)
      · Required directories exist (backend/, frontend/)
      · Entry point files exist on disk
      · Platform compatibility range is satisfied
      · Backend exports a FastAPI router
      · Frontend exports moduleConfig and a default component

    \b
    Examples:
        techforge validate-module
        techforge validate-module modules/installed/hello_world
        techforge validate-module . --platform-version 1.2.0
        techforge validate-module . --strict
    """
    path = Path(module_path).resolve()
    print_header(f"Validate Module: {path.name}")
    print_info(f"Path:             [path]{path}[/path]")
    print_info(f"Platform version: [version]{platform_version}[/version]")
    console.print()

    report = ModuleCLIValidator.validate(path, platform_version)

    # ── Results table ─────────────────────────────────────────────────────────
    table = Table(
        show_header=True,
        header_style="bold white",
        border_style="dim",
        show_lines=False,
        pad_edge=True,
    )
    table.add_column("Check", style="white", no_wrap=True)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Detail", style="dim")

    for check in report.checks:
        if check.passed:
            status = "[pass]✓ PASS[/pass]"
        elif check.level == "warning":
            status = "[warn]⚠ WARN[/warn]"
        else:
            status = "[fail]✗ FAIL[/fail]"
        table.add_row(check.name, status, check.message)

    console.print(table)

    # ── Summary ───────────────────────────────────────────────────────────────
    print_section("Summary")
    total    = len(report.checks)
    passed   = sum(1 for c in report.checks if c.passed)
    errors   = report.error_count
    warnings = report.warning_count

    console.print(f"  Checks:   [muted]{total}[/muted]")
    console.print(f"  Passed:   [pass]{passed}[/pass]")
    if errors:
        console.print(f"  Errors:   [fail]{errors}[/fail]")
    if warnings:
        console.print(f"  Warnings: [warn]{warnings}[/warn]")

    console.print()

    overall_fail = not report.passed or (strict and warnings > 0)

    if overall_fail:
        if not report.passed:
            print_error("Module validation FAILED — fix errors before installing.")
        else:
            print_error("Module has warnings and --strict is enabled.")
        raise click.exceptions.Exit(1)
    else:
        if warnings:
            print_warning("Module valid with warnings.")
        else:
            print_success("Module is valid and ready to install.")
    console.print()
