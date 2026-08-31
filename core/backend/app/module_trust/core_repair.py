"""Core repair check — Fase 16 §33.

Aplica o mesmo mecanismo de integrity manifest da Fase 10 (por-módulo) ao
código do próprio Core — só verifica, não tenta restaurar nada
automaticamente (spec §33: "Não implementar reparo agressivo sem
integridade verificada").
"""
from __future__ import annotations

import json
from pathlib import Path

from app.core.paths import install_dir
from app.module_trust.integrity import (
    IntegrityResult,
    IntegrityStatus,
    diff_manifests,
    generate_integrity_manifest,
)

CORE_MANIFEST_FILENAME = "core-integrity.json"

# Diretórios de código efetivamente distribuídos com o Core — não a raiz
# inteira da instalação, que em árvore de dev também contém .git,
# .venv, node_modules, modules/installed (dados do usuário) etc.
CORE_SOURCE_DIRS = (
    "core/backend/app",
    "cli/techforge_cli",
    "sdk/python/techforge_sdk",
    "launcher/techforge_launcher",
)


def core_manifest_path() -> Path:
    return install_dir() / CORE_MANIFEST_FILENAME


def _current_core_files() -> dict[str, str]:
    files: dict[str, str] = {}
    for rel_dir in CORE_SOURCE_DIRS:
        sub = generate_integrity_manifest(install_dir() / rel_dir)["files"]
        for path, digest in sub.items():
            files[f"{rel_dir}/{path}"] = digest
    return files


def write_core_manifest() -> Path:
    """Gera e escreve core-integrity.json na raiz da instalação. Rodar após
    um build limpo (mesmo momento do packaging, Slice 7), não em runtime."""
    manifest = {"algorithm": "sha256", "files": _current_core_files()}
    target = core_manifest_path()
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return target


def verify_core_integrity() -> IntegrityResult:
    manifest_path = core_manifest_path()
    if not manifest_path.is_file():
        return IntegrityResult(
            IntegrityStatus.INVALID_MANIFEST,
            detail=f"{CORE_MANIFEST_FILENAME} not found — gere um após um build limpo",
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_files = manifest["files"]
        if not isinstance(expected_files, dict):
            raise ValueError("files must be a dict")
    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
        return IntegrityResult(IntegrityStatus.INVALID_MANIFEST,
                               detail=f"malformed {CORE_MANIFEST_FILENAME}: {exc}")

    return diff_manifests(expected_files, _current_core_files())
