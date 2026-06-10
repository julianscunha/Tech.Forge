"""
TechForge CLI — Main entry point
==================================
Assembles all CLI commands into the `techforge` command group.

Available commands:
    techforge create-module    — scaffold a new module
    techforge validate-module  — validate a module directory
    techforge package-module   — build a .mod archive

Usage:
    techforge --help
    techforge create-module --help
"""
import click
from techforge_cli.console import print_banner
from techforge_cli.commands.create_module  import create_module_cmd
from techforge_cli.commands.validate_module import validate_module_cmd
from techforge_cli.commands.package_module  import package_module_cmd


@click.group()
@click.version_option("1.0.0", prog_name="TechForge CLI")
def cli():
    """
    TechForge Module Development CLI

    \b
    Commands:
      create-module    Scaffold a new module from the official template
      validate-module  Validate a module directory and print a report
      package-module   Build a distributable .mod archive

    \b
    Examples:
      techforge create-module
      techforge validate-module modules/installed/hello_world
      techforge package-module . --output dist/

    \b
    Phase 4 additions (coming):
      techforge publish-module   — upload to Marketplace
      techforge install-module   — install from Marketplace
    """
    pass


cli.add_command(create_module_cmd)
cli.add_command(validate_module_cmd)
cli.add_command(package_module_cmd)


def main():
    print_banner()
    cli()


if __name__ == "__main__":
    main()
