"""Fase 15 §23 — validação de versionamento MAJOR.MINOR.PATCH.

Reusa `packaging.version` (já dependência, Fase 12) em vez de escrever um
parser SemVer próprio.
"""
from __future__ import annotations

from packaging.version import InvalidVersion, Version


def is_valid_semver(value: str) -> bool:
    try:
        Version(value)
        return True
    except InvalidVersion:
        return False
