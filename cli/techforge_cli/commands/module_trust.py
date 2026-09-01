"""techforge verify-module / integrity check / publishers list|show — Fase 10 §23/§24.
techforge trust generate-keypair / sign-module — Fase 17 §7/§12.

Consome a API do Core (/api/v1/modules/{id}/verify|integrity|trust,
/api/v1/publishers*) — nenhuma lógica de verificação duplicada aqui.

sign-module/generate-keypair são operações locais de criptografia (não
tocam a plataforma rodando): o publisher assina o módulo com sua chave
privada ANTES de empacotar/distribuir — a chave privada nunca entra no
Core em runtime (spec §12).
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import click
import yaml
from rich.table import Table

from techforge_cli.config import CORE_BASE_URL as _CORE
from techforge_cli.console import console, print_error, print_info, print_success, print_warning

# `app` vive em core/backend/, irmão de cli/ no monorepo Tech.Forge — mesmo
# padrão de resolução de path usado por techforge_cli/packager/builder.py.
_CORE_BACKEND = Path(__file__).resolve().parents[3] / "core" / "backend"
if str(_CORE_BACKEND) not in sys.path:
    sys.path.insert(0, str(_CORE_BACKEND))


def _get(path: str):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{_CORE}{path}", timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print_error(exc.read().decode("utf-8", errors="replace"))
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge platform start'.")
        raise SystemExit(1)


def _post(path: str):
    import urllib.error
    import urllib.request
    req = urllib.request.Request(f"{_CORE}{path}", data=b"", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print_error(exc.read().decode("utf-8", errors="replace"))
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print_error(f"Plataforma não acessível ({exc.reason}). Use 'techforge platform start'.")
        raise SystemExit(1)


def _print_integrity_result(result: dict) -> None:
    console.print(f"[cyan]{result['module_id']}[/cyan] → {result['status']}")
    if result.get("modified_files"):
        console.print(f"  modified: {result['modified_files']}")
    if result.get("missing_files"):
        console.print(f"  missing: {result['missing_files']}")
    if result.get("unexpected_files"):
        console.print(f"  unexpected: {result['unexpected_files']}")


@click.command("verify-module")
@click.argument("module_id")
def verify_module_cmd(module_id):
    """Reverify an installed module's integrity on demand."""
    _print_integrity_result(_post(f"/modules/{module_id}/verify"))


@click.group("integrity")
def integrity_cmd():
    """Inspect module integrity manifests."""


@integrity_cmd.command("check")
@click.argument("module_id")
def integrity_check_cmd(module_id):
    """Show a module's current integrity status (read-only, no side effects)."""
    _print_integrity_result(_get(f"/modules/{module_id}/integrity"))


@click.group("publishers")
def publishers_cmd():
    """Inspect the Publisher Registry."""


@publishers_cmd.command("list")
def publishers_list_cmd():
    """List all known publishers."""
    publishers = _get("/publishers")
    if not publishers:
        print_info("Nenhum publisher registrado.")
        return
    table = Table(show_header=True, header_style="bold white", border_style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Trust Status")
    for p in publishers:
        table.add_row(p["id"], p["name"], p["type"], p["trust_status"])
    console.print(table)


@publishers_cmd.command("show")
@click.argument("publisher_id")
def publishers_show_cmd(publisher_id):
    """Show details of one publisher."""
    p = _get(f"/publishers/{publisher_id}")
    console.print(f"[cyan]{p['id']}[/cyan]  {p['name']}")
    console.print(f"  Type:         {p['type']}")
    console.print(f"  Trust Status: {p['trust_status']}")
    console.print(f"  Public key:   {p.get('public_key') or '(none)'}")


# ── Fase 17 §7/§12 — assinatura Ed25519 (operações locais, sem API) ────────────

@click.group("trust")
def trust_cmd():
    """Manage Ed25519 keypairs and inspect trust (Fase 17)."""


@trust_cmd.command("publishers")
def trust_publishers_cmd():
    """List all known publishers (alias of `publishers list`, under `trust`)."""
    publishers_list_cmd.callback()


@trust_cmd.command("generate-keypair")
@click.option("--output-dir", default=".", type=click.Path(file_okay=False),
              help="Directory to write the keypair files into.")
@click.option("--name", default="techforge-signing", show_default=True,
              help="Filename prefix for the generated keypair.")
def generate_keypair_cmd(output_dir, name):
    """Generate a new Ed25519 keypair for signing modules.

    The private key must be kept offline and NEVER committed to a
    repository or uploaded to the Core — only the public key goes into
    the Publisher Registry.
    """
    from app.module_trust.signature import generate_ed25519_keypair

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    private_path = out / f"{name}_private.pem"
    public_path = out / f"{name}_public.pem"

    private_pem, public_pem = generate_ed25519_keypair()
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)

    print_success(f"Keypair generated: {private_path.name}, {public_path.name}")
    print_warning(f"Keep {private_path.name} offline — never commit it or send it to the Core.")
    print_info("Register the public key with your Publisher entry (public_key field).")


@click.command("sign-module")
@click.argument("module_path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--key", "private_key_path", required=True,
              type=click.Path(exists=True, dir_okay=False),
              help="Path to the Ed25519 private key PEM file.")
def sign_module_cmd(module_path, private_key_path):
    """Sign a module's manifest.yaml with an Ed25519 private key.

    Run this BEFORE `techforge package-module` — the signature must be
    part of manifest.yaml when the .mod archive is built.
    """
    from app.module_trust.signature import Ed25519SignatureProvider, canonical_manifest_bytes

    manifest_path = Path(module_path) / "manifest.yaml"
    if not manifest_path.is_file():
        print_error(f"manifest.yaml not found in {module_path}")
        raise click.exceptions.Exit(1)

    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    private_pem = Path(private_key_path).read_bytes()

    try:
        signature = Ed25519SignatureProvider().sign(canonical_manifest_bytes(raw), private_pem)
    except ValueError as exc:
        print_error(str(exc))
        raise click.exceptions.Exit(1)

    raw["signature"] = base64.b64encode(signature).decode()
    manifest_path.write_text(yaml.dump(raw, sort_keys=False), encoding="utf-8")

    print_success(f"Module {raw.get('id', module_path)!r} signed — manifest.yaml updated.")
