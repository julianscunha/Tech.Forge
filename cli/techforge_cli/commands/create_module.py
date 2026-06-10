"""techforge create-module — interactive module scaffold generator."""
from __future__ import annotations

from pathlib import Path
import click
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from techforge_cli.console import (
    console, print_header, print_success, print_error,
    print_info, print_muted, print_section,
)
from techforge_cli.templates.generator import ModuleSpec, TemplateGenerator


@click.command("create-module")
@click.option("--id",          "module_id",    default=None, help="Module identifier (snake_case)")
@click.option("--name",        "module_name",  default=None, help="Human-readable display name")
@click.option("--category",    default=None,   help="Module category (e.g. Backup, Cloud)")
@click.option("--vendor",      default=None,   help="Vendor / company name")
@click.option("--author",      default=None,   help="Author name")
@click.option("--description", default=None,   help="One-line description")
@click.option("--output",      default=".",    help="Parent directory for the new module", show_default=True)
@click.option("--yes", "-y",   is_flag=True,   help="Skip confirmation prompt")
def create_module_cmd(
    module_id, module_name, category, vendor, author, description, output, yes
):
    """
    Scaffold a new TechForge module interactively.

    Generates the complete directory structure, manifest.yaml,
    backend stub, frontend stub, tests, and README.

    \b
    Examples:
        techforge create-module
        techforge create-module --id my_tool --name "My Tool" --category Backup
        techforge create-module --output modules/installed
    """
    print_header("Create Module")
    console.print("  [muted]Scaffolds a new TechForge module from the official template.[/muted]\n")

    # ── Collect values (flags override interactive prompts) ───────────────────
    if module_id is None:
        module_id = Prompt.ask("  [cyan]Module id[/cyan] [muted](snake_case)[/muted]")
    if module_name is None:
        module_name = Prompt.ask("  [cyan]Name[/cyan]        [muted](display name)[/muted]",
                                  default=module_id.replace("_", " ").title())
    if category is None:
        category = Prompt.ask("  [cyan]Category[/cyan]    [muted](Backup / Cloud / Virtualization / …)[/muted]")
    if vendor is None:
        vendor = Prompt.ask("  [cyan]Vendor[/cyan]      [muted](company or author name)[/muted]")
    if author is None:
        author = Prompt.ask("  [cyan]Author[/cyan]      [muted](full name)[/muted]", default=vendor)
    if description is None:
        description = Prompt.ask("  [cyan]Description[/cyan] [muted](one line)[/muted]",
                                  default=f"{module_name} module for TechForge.")

    spec = ModuleSpec(
        id=module_id.strip().lower().replace(" ", "_").replace("-", "_"),
        name=module_name.strip(),
        category=category.strip(),
        vendor=vendor.strip(),
        author=author.strip(),
        description=description.strip(),
    )

    # ── Validate spec ─────────────────────────────────────────────────────────
    errors = spec.validate()
    if errors:
        print_section("Validation errors")
        for err in errors:
            print_error(err)
        raise click.Abort()

    # ── Preview ───────────────────────────────────────────────────────────────
    output_dir = Path(output).resolve()
    target = output_dir / spec.id

    print_section("Module summary")
    console.print(Panel(
        f"[muted]id:[/muted]          [accent]{spec.id}[/accent]\n"
        f"[muted]name:[/muted]        {spec.name}\n"
        f"[muted]version:[/muted]     {spec.version}\n"
        f"[muted]category:[/muted]    {spec.category}\n"
        f"[muted]vendor:[/muted]      {spec.vendor}\n"
        f"[muted]author:[/muted]      {spec.author}\n"
        f"[muted]description:[/muted] {spec.description}\n"
        f"[muted]output:[/muted]      [path]{target}[/path]",
        border_style="blue",
        padding=(0, 2),
    ))

    if not yes:
        confirmed = Confirm.ask("\n  Create module?", default=True)
        if not confirmed:
            console.print("  [muted]Aborted.[/muted]")
            raise click.Abort()

    # ── Generate ──────────────────────────────────────────────────────────────
    try:
        gen = TemplateGenerator(output_dir)
        module_dir = gen.generate(spec)
    except FileExistsError as exc:
        print_error(str(exc))
        raise click.ClickException(str(exc))

    # ── Result ────────────────────────────────────────────────────────────────
    print_section("Files created")
    for f in sorted(module_dir.rglob("*")):
        if f.is_file():
            rel = f.relative_to(output_dir)
            print_muted(str(rel))

    console.print()
    print_success(f"Module [accent]{spec.id}[/accent] created at [path]{module_dir}[/path]")
    console.print()
    print_info("Next steps:")
    print_muted(f"  1. cd {module_dir}")
    print_muted(f"  2. techforge validate-module .")
    print_muted(f"  3. cp -r {module_dir} <techforge_root>/modules/installed/")
    print_muted(f"  4. Restart the TechForge backend")
    console.print()
