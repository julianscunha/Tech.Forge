"""
Module Trust — Fase 10
=========================
Integridade de pacote (hash por-arquivo), Publisher Registry, Trust
Level e assinatura digital (abstração) para módulos instalados.
"""
from app.module_trust.integrity import (
    IntegrityStatus, IntegrityResult,
    generate_integrity_manifest, verify_integrity, write_integrity_manifest,
)

__all__ = [
    "IntegrityStatus", "IntegrityResult",
    "generate_integrity_manifest", "verify_integrity", "write_integrity_manifest",
]
