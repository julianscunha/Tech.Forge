"""techforge repair-check — Fase 16 §33.

Verifica a integridade dos arquivos do Core (não de módulos — isso já é
`techforge integrity check`). Só verifica; não tenta restaurar nada
automaticamente (spec §33: "Não implementar reparo agressivo sem
integridade verificada").
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

from techforge_cli.console import console, print_error, print_success, print_warning

_CORE = Path(__file__).resolve().parent.parent.parent.parent / "core" / "backend"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from app.module_trust.core_repair import (  # noqa: E402
    CORE_MANIFEST_FILENAME,
    core_manifest_path,
    verify_core_integrity,
    write_core_manifest,
)
from app.module_trust.integrity import IntegrityStatus  # noqa: E402


@click.command("repair-check")
@click.option("--generate", is_flag=True,
              help="Gerar o manifesto de integridade a partir do estado atual (rodar após um build limpo).")
def repair_check_cmd(generate: bool) -> None:
    """Verificar a integridade da instalação do Core."""
    if generate:
        path = write_core_manifest()
        print_success(f"Manifesto de integridade gerado em {path}")
        return

    result = verify_core_integrity()

    if result.status == IntegrityStatus.INVALID_MANIFEST:
        print_warning(
            f"{CORE_MANIFEST_FILENAME} não encontrado em {core_manifest_path()}.\n"
            f"Gere um com `techforge repair-check --generate` após um build limpo."
        )
        raise SystemExit(2)

    if result.status == IntegrityStatus.VALID:
        print_success("Instalação íntegra — OK.")
        return

    print_error(f"Instalação divergente do manifesto ({result.status.value}):")
    for path in result.missing_files:
        console.print(f"  [red]faltando[/red]  {path}")
    for path in result.modified_files:
        console.print(f"  [yellow]modificado[/yellow]  {path}")
    for path in result.unexpected_files:
        console.print(f"  [cyan]inesperado[/cyan]  {path}")
    raise SystemExit(1)
