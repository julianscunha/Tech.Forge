"""techforge modules — list/show/validate installed modules (Fase 3 §19).

Reuses the Core engine (app.module_engine ManifestParser + ModuleValidator).
No validation logic is duplicated here, per spec §19.
"""
from __future__ import annotations

import sys
from pathlib import Path

import json

import click
from rich.table import Table

from techforge_cli.console import (
    console, print_header, print_error, print_success, print_info,
)

# Core engine — added to path so the CLI can run from any checkout
_CORE = Path(__file__).resolve().parent.parent.parent.parent / "core" / "backend"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from app.module_engine.manifest import ManifestParser, ManifestError  # noqa: E402
from app.module_engine.validator import ModuleValidator  # noqa: E402


def _scan(modules_dir: Path):
    """Scan a modules directory using the Core ManifestParser.

    Returns a list of (dir_name, parsed_manifest | error_string).
    Invalid modules are reported but never crash the scan.
    """
    results = []
    if not modules_dir.is_dir():
        return results
    for entry in sorted(modules_dir.iterdir()):
        if not entry.is_dir():
            continue
        try:
            results.append((entry.name, ManifestParser.parse(entry)))
        except ManifestError as exc:
            results.append((entry.name, str(exc)))
        except Exception as exc:  # defensive: keep scanning
            results.append((entry.name, f"unexpected error: {exc}"))
    return results


@click.group("modules")
def modules_cmd():
    """Inspect and validate TechForge modules."""


@modules_cmd.command("list")
@click.option("--modules-dir", type=click.Path(exists=True, file_okay=False),
              default=None, help="Modules directory (default: <repo>/modules/installed)")
def list_cmd(modules_dir):
    """List discovered modules and their status."""
    base = Path(modules_dir) if modules_dir else (
        Path(__file__).resolve().parent.parent.parent.parent / "modules" / "installed"
    )
    print_header("TechForge Modules")
    rows = _scan(base)
    if not rows:
        print_info(f"No modules found in {base}")
        return

    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Type")
    table.add_column("Status")

    valid = 0
    for name, item in rows:
        if isinstance(item, Exception) or isinstance(item, str):
            table.add_row(name, "-", "-", "-", "[red]INVALID[/red]")
            console.print(f"[dim]  └ {name}: {item}[/dim]") if False else None
        else:
            valid += 1
            module_type = item.raw.get("module_type", "application")
            table.add_row(item.id, item.name, item.version, module_type,
                          "[green]OK[/green]")
    console.print(table)
    print_info(f"{valid}/{len(rows)} valid")


@modules_cmd.command("show")
@click.argument("module_id")
@click.option("--modules-dir", type=click.Path(exists=True, file_okay=False),
              default=None)
def show_cmd(module_id, modules_dir):
    """Show details of a single module by id."""
    base = Path(modules_dir) if modules_dir else (
        Path(__file__).resolve().parent.parent.parent.parent / "modules" / "installed"
    )
    for name, item in _scan(base):
        if not isinstance(item, (Exception, str)) and item.id == module_id:
            print_header(f"Module: {item.name}")
            module_type = item.raw.get("module_type", "application")
            print_info(f"Id:            [cyan]{item.id}[/cyan]")
            print_info(f"Name:          {item.name}")
            print_info(f"Version:       [version]{item.version}[/version]")
            print_info(f"Type:          {module_type}")
            print_info(f"Category:      {item.category}")
            print_info(f"Vendor:        {item.vendor}")
            print_info(f"Entry backend: [path]{item.entry_backend}[/path]")
            print_info(f"Entry frontend:[path]{item.entry_frontend}[/path]")
            return
    print_error(f"Module '{module_id}' not found in {base}")
    raise SystemExit(1)


@modules_cmd.command("validate")
@click.argument("module_path", type=click.Path(exists=True, file_okay=False))
@click.option("--platform-version", default="1.0.0", show_default=True)
def validate_cmd(module_path, platform_version):
    """Validate a module directory using the Core validator."""
    result = ModuleValidator.validate(Path(module_path).resolve(), platform_version)
    if result.is_valid:
        print_success(f"Module is VALID ({result.status.value})")
    else:
        print_error(f"Module is INVALID ({result.status.value})")
        for err in result.errors:
            console.print(f"  [red]✗[/red] {err}")
        raise SystemExit(1)


# ── Lifecycle (Fase 4 §19) — delegates to Core API ───────────────────────────

def _core_post(path: str) -> dict:
    import urllib.request
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1{path}", data=b"", method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"ok": False, "detail": exc.read().decode("utf-8", errors="replace")}
    except urllib.error.URLError as exc:
        return {"ok": False, "detail": f"Plataforma não acessível ({exc.reason}). "
                                       f"Use 'techforge platform start'."}


def _lifecycle(action: str, module_id: str) -> None:
    result = _core_post(f"/marketplace/{action}/{module_id}")
    if result.get("ok"):
        print_success(result.get("message", f"{action} ok"))
    else:
        print_error(result.get("detail", f"Falha ao {action} '{module_id}'."))
        raise SystemExit(1)


@modules_cmd.command("activate")
@click.argument("module_id")
def activate_cmd(module_id):
    """Activate an installed (disabled) module via the Core API."""
    _lifecycle("activate", module_id)


@modules_cmd.command("deactivate")
@click.argument("module_id")
def deactivate_cmd(module_id):
    """Deactivate a module — files kept, resources saved."""
    _lifecycle("deactivate", module_id)


@modules_cmd.command("remove")
@click.argument("module_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def remove_cmd(module_id, yes):
    """Permanently remove a module (physical deletion) via the Core API."""
    if not yes:
        click.confirm(
            f"Remover PERMANENTEMENTE o módulo '{module_id}' e seus arquivos?",
            abort=True,
        )
    import urllib.request
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/marketplace/remove/{module_id}",
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print_success(f"Módulo '{module_id}' removido.")
    except urllib.error.HTTPError as exc:
        print_error(exc.read().decode("utf-8", errors="replace"))
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível: {exc.reason}")
        raise SystemExit(1)


# ── Dependency Governance (Fase 8.1 §24) — delegates to Core API ────────────

def _core_get(path: str):
    import urllib.request
    import urllib.error
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:8000/api/v1{path}", timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge platform start'.")
        raise SystemExit(1)


@modules_cmd.command("dependencies")
@click.argument("module_id")
def dependencies_cmd(module_id):
    """Show resolved dependencies (status) of a module."""
    deps = _core_get(f"/modules/{module_id}/dependencies")
    if not deps:
        print_info(f"'{module_id}' não declara dependências.")
        return
    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("Target", style="cyan")
    table.add_column("Type")
    table.add_column("Required")
    table.add_column("Version range")
    table.add_column("Status")
    for d in deps:
        table.add_row(d["target_id"], d["target_type"], str(d["required"]),
                      d.get("version_range") or "-", d.get("status") or "-")
    console.print(table)


@modules_cmd.command("dependents")
@click.argument("module_id")
def dependents_cmd(module_id):
    """List installed modules that depend on this one."""
    dependents = _core_get(f"/modules/{module_id}/dependents")
    if not dependents:
        print_info(f"Nenhum módulo instalado depende de '{module_id}'.")
        return
    for dep in dependents:
        console.print(f"  [cyan]{dep}[/cyan]")


@modules_cmd.command("validate-dependencies")
def validate_dependencies_cmd():
    """Validate declared dependencies of every installed module."""
    report = _core_get("/dependencies/validate")
    if not report:
        print_info("Nenhum módulo instalado declara dependências.")
        return
    failed = False
    for module_id, checks in report.items():
        console.print(f"[cyan]{module_id}[/cyan]")
        for c in checks:
            icon = "[green]✓[/green]" if c["passed"] else "[red]✗[/red]"
            console.print(f"  {icon} {c['name']}: {c['detail']}")
            failed = failed or (not c["passed"] and c["required"])
    if failed:
        raise SystemExit(1)


@modules_cmd.command("graph")
def graph_cmd():
    """Print the dependency graph as raw Mermaid flowchart syntax."""
    result = _core_get("/dependencies/graph")
    console.print(result.get("mermaid", ""))


# ── Module Configuration (Fase 12 §29/§30) — delegates to Core API ──────────

def _parse_set_values(pairs: tuple[str, ...]) -> dict:
    values = {}
    for pair in pairs:
        if "=" not in pair:
            print_error(f"--set precisa de 'chave=valor', recebido: {pair!r}")
            raise SystemExit(1)
        key, _, raw_value = pair.partition("=")
        try:
            values[key] = json.loads(raw_value)
        except json.JSONDecodeError:
            values[key] = raw_value  # string literal (ex.: --set nome=producao)
    return values


def _core_put_json(path: str, payload: dict) -> dict:
    import urllib.request
    import urllib.error
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1{path}", data=body, method="PUT",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print_error(exc.read().decode("utf-8", errors="replace"))
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge platform start'.")
        raise SystemExit(1)


def _core_post_json(path: str, payload: dict) -> dict:
    import urllib.request
    import urllib.error
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1{path}", data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print_error(exc.read().decode("utf-8", errors="replace"))
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge platform start'.")
        raise SystemExit(1)


@modules_cmd.command("config")
@click.argument("module_id")
@click.option("--set", "set_pairs", multiple=True, metavar="CHAVE=VALOR",
              help="Define um valor (repetível). Sem --set, apenas mostra a config atual.")
def config_cmd(module_id, set_pairs):
    """Show or update a module's configuration."""
    if not set_pairs:
        result = _core_get(f"/modules/{module_id}/config")
    else:
        result = _core_put_json(f"/modules/{module_id}/config", {"values": _parse_set_values(set_pairs)})
    for key, value in result.get("values", {}).items():
        console.print(f"  {key} = {value}")


@modules_cmd.command("config-validate")
@click.argument("module_id")
@click.option("--set", "set_pairs", multiple=True, metavar="CHAVE=VALOR", required=True,
              help="Valor a validar (repetível).")
def config_validate_cmd(module_id, set_pairs):
    """Validate a configuration payload without persisting it."""
    result = _core_post_json(
        f"/modules/{module_id}/config/validate", {"values": _parse_set_values(set_pairs)}
    )
    if result.get("valid"):
        print_success("Configuração válida.")
        for key, value in result.get("values", {}).items():
            console.print(f"  {key} = {value}")
    else:
        print_error("Configuração inválida.")
        raise SystemExit(1)
