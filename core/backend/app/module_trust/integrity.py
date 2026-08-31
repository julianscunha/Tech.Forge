"""
Integrity Manifest — Fase 10 §5/§6
======================================
Hash SHA-256 por arquivo de um pacote de módulo instalado — permite
detectar depois se um arquivo específico foi modificado, removido, ou
se um arquivo não declarado apareceu. Diferente do checksum de
`.mod` inteiro já existente em `package_manager/repository.py` (aquele
é do pacote como um todo, no repositório; este é dos arquivos já
instalados em disco).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

INTEGRITY_FILENAME = "integrity.json"

# Arquivos/diretórios nunca entram no hash: dados de runtime do módulo,
# caches, o próprio integrity.json. Fase 12 §20 — cache/exports/temp são
# paths oficiais de runtime, não código do módulo.
_EXCLUDED_DIR_PREFIXES = ("data/", "cache/", "exports/", "temp/", "__pycache__/")
_EXCLUDED_SUFFIXES = (".pyc",)
_EXCLUDED_NAMES = (INTEGRITY_FILENAME,)


def _is_excluded(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    if normalized in _EXCLUDED_NAMES:
        return True
    if any(normalized.startswith(prefix) or f"/{prefix}" in normalized
           for prefix in _EXCLUDED_DIR_PREFIXES):
        return True
    if normalized.endswith(_EXCLUDED_SUFFIXES):
        return True
    return False


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _scan_package_files(package_dir: Path) -> dict[str, str]:
    """Retorna {caminho_relativo_posix: sha256_hex} de todo arquivo relevante."""
    result: dict[str, str] = {}
    for path in package_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(package_dir).as_posix()
        if _is_excluded(rel):
            continue
        result[rel] = _hash_file(path)
    return result


def generate_integrity_manifest(package_dir: Path) -> dict:
    """Gera o dict do integrity manifest (algorithm + files) — não escreve em disco."""
    return {"algorithm": "sha256", "files": _scan_package_files(package_dir)}


def write_integrity_manifest(package_dir: Path) -> Path:
    """Gera e escreve integrity.json na raiz de package_dir. Retorna o Path escrito."""
    manifest = generate_integrity_manifest(package_dir)
    target = package_dir / INTEGRITY_FILENAME
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return target


class IntegrityStatus(str, Enum):
    VALID            = "VALID"
    MODIFIED         = "MODIFIED"
    MISSING_FILE     = "MISSING_FILE"
    UNEXPECTED_FILE  = "UNEXPECTED_FILE"
    INVALID_MANIFEST = "INVALID_MANIFEST"


@dataclass
class IntegrityResult:
    status:            IntegrityStatus
    modified_files:    list[str] = field(default_factory=list)
    missing_files:     list[str] = field(default_factory=list)
    unexpected_files:  list[str] = field(default_factory=list)
    detail:            str = ""


def diff_manifests(expected_files: dict[str, str], current_files: dict[str, str]) -> IntegrityResult:
    """Compara dois mapas {caminho: sha256} e agrega num único IntegrityResult.

    Prioridade do status quando há múltiplos problemas:
    MISSING_FILE > MODIFIED > UNEXPECTED_FILE > VALID. Compartilhado por
    `verify_integrity` (por módulo) e `app/module_trust/core_repair.py`
    (Fase 16 §33 — mesmo mecanismo aplicado ao Core, não só a módulos).
    """
    missing    = sorted(set(expected_files) - set(current_files))
    unexpected = sorted(set(current_files) - set(expected_files))
    modified   = sorted(
        path for path in (set(expected_files) & set(current_files))
        if expected_files[path] != current_files[path]
    )

    if missing:
        status = IntegrityStatus.MISSING_FILE
    elif modified:
        status = IntegrityStatus.MODIFIED
    elif unexpected:
        status = IntegrityStatus.UNEXPECTED_FILE
    else:
        status = IntegrityStatus.VALID

    return IntegrityResult(status, modified_files=modified,
                           missing_files=missing, unexpected_files=unexpected)


def verify_integrity(package_dir: Path) -> IntegrityResult:
    """Lê integrity.json de package_dir e compara contra os arquivos reais em disco agora."""
    manifest_path = package_dir / INTEGRITY_FILENAME
    if not manifest_path.is_file():
        return IntegrityResult(IntegrityStatus.INVALID_MANIFEST,
                               detail=f"{INTEGRITY_FILENAME} not found")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_files = manifest["files"]
        if not isinstance(expected_files, dict):
            raise ValueError("files must be a dict")
    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
        return IntegrityResult(IntegrityStatus.INVALID_MANIFEST,
                               detail=f"malformed integrity.json: {exc}")

    current_files = _scan_package_files(package_dir)
    return diff_manifests(expected_files, current_files)
