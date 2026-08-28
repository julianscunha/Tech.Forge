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
from app.module_trust.publisher import PublisherType, PublisherTrustStatus
from app.module_trust.trust import TrustLevel, TrustResolver
from app.module_trust.signature import (
    SignatureStatus, SignatureProvider, NoOpSignatureProvider, default_signature_provider,
)

__all__ = [
    "IntegrityStatus", "IntegrityResult",
    "generate_integrity_manifest", "verify_integrity", "write_integrity_manifest",
    "PublisherType", "PublisherTrustStatus",
    "TrustLevel", "TrustResolver",
    "SignatureStatus", "SignatureProvider", "NoOpSignatureProvider", "default_signature_provider",
]
