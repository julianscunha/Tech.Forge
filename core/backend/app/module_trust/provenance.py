"""
Package Provenance — Fase 10 §14
====================================
Mapeia o `source_type` já existente em `ParsedManifest`/`Module` (Fase
4: local|catalog|development) para os nomes de origem da spec da Fase
10. Não introduz coluna nova — `Module.source_type`/`source_location`
já existem, só nunca eram propagados de verdade (ver Parte A.2).
"""
from __future__ import annotations

from enum import Enum


class InstallSource(str, Enum):
    LOCAL_FILE        = "LOCAL_FILE"
    LOCAL_DEVELOPMENT = "LOCAL_DEVELOPMENT"
    INTERNAL_CATALOG  = "INTERNAL_CATALOG"
    REMOTE_CATALOG    = "REMOTE_CATALOG"


_SOURCE_TYPE_MAP = {
    "local":       InstallSource.LOCAL_FILE,
    "development": InstallSource.LOCAL_DEVELOPMENT,
    "catalog":     InstallSource.INTERNAL_CATALOG,
}


def resolve_install_source(source_type: str) -> InstallSource:
    """Mapeia o `source_type` do manifest/DB para o InstallSource da spec.
    Valor desconhecido cai em LOCAL_FILE (mais conservador — nunca assume
    origem remota sem declaração explícita)."""
    return _SOURCE_TYPE_MAP.get(source_type, InstallSource.LOCAL_FILE)
