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
from techforge_cli.commands.modules        import modules_cmd
from techforge_cli.commands.docs           import docs_cmd
from techforge_cli.commands.services       import services_cmd
from techforge_cli.commands.runtime        import runtime_cmd
from techforge_cli.commands.module_trust   import (
    verify_module_cmd, integrity_cmd, publishers_cmd,
)
from techforge_cli.commands.platform        import start_cmd, stop_cmd, status_cmd, logs_cmd, dev_cmd
from techforge_cli.commands.catalog         import catalog_cmd
from techforge_cli.commands.storage         import storage_cmd


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
cli.add_command(modules_cmd)    # Phase 3 — modules list/show/validate
cli.add_command(docs_cmd)       # Phase 5 — docs list/search/get/export-context
cli.add_command(services_cmd)   # Fase 8 — services list/show/capabilities/contract/status
cli.add_command(runtime_cmd)    # Fase 9 — runtime status/modules/module/initialize
cli.add_command(verify_module_cmd)  # Fase 10 — verify-module
cli.add_command(integrity_cmd)      # Fase 10 — integrity check
cli.add_command(publishers_cmd)     # Fase 10 — publishers list/show
cli.add_command(start_cmd)     # Phase 6
cli.add_command(stop_cmd)      # Phase 6
cli.add_command(status_cmd)    # Phase 6
cli.add_command(logs_cmd)      # Fase 6 §16 — techforge logs
cli.add_command(dev_cmd)       # Fase 6 §17 — techforge dev
cli.add_command(catalog_cmd)   # Fase 11 Slice 6 — catalog (list/search/show/sources/build-index)
cli.add_command(storage_cmd)   # Fase 12 Slice 1 — storage status


def main():
    print_banner()
    cli()


if __name__ == "__main__":
    main()
