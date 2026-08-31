"""
Module Trust — Fase 10
=========================
Integridade de pacote (hash por-arquivo), Publisher Registry, Trust
Level e assinatura digital (abstração) para módulos instalados.
"""
from app.module_trust.integrity import (
    IntegrityResult,
    IntegrityStatus,
    generate_integrity_manifest,
    verify_integrity,
    write_integrity_manifest,
)
from app.module_trust.provenance import InstallSource, resolve_install_source
from app.module_trust.publisher import PublisherTrustStatus, PublisherType
from app.module_trust.security_policy import (
    DesktopSecurityPolicy,
    SecurityPolicy,
    ServerSecurityPolicy,
    default_security_policy,
)
from app.module_trust.signature import (
    Ed25519SignatureProvider,
    NoOpSignatureProvider,
    SignatureProvider,
    SignatureStatus,
    canonical_manifest_bytes,
    default_signature_provider,
    generate_ed25519_keypair,
)
from app.module_trust.trust import TrustLevel, TrustResolver
from app.module_trust.verification import verify_module_integrity

__all__ = [
    "IntegrityStatus", "IntegrityResult",
    "generate_integrity_manifest", "verify_integrity", "write_integrity_manifest",
    "InstallSource", "resolve_install_source",
    "PublisherType", "PublisherTrustStatus",
    "TrustLevel", "TrustResolver",
    "SignatureStatus", "SignatureProvider", "NoOpSignatureProvider",
    "Ed25519SignatureProvider", "default_signature_provider",
    "generate_ed25519_keypair", "canonical_manifest_bytes",
    "verify_module_integrity",
    "SecurityPolicy", "DesktopSecurityPolicy", "ServerSecurityPolicy", "default_security_policy",
]
