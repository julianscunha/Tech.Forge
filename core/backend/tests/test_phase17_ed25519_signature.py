"""Fase 17 Slice 2 — assinatura Ed25519 real (spec §7/§12).

Threat model (skill security-and-hardening): Spoofing/Tampering — um
pacote de publisher não verificado, ou adulterado depois de assinado,
sendo tratado como confiável. Boundary: `signature` declarada no
manifest de um módulo, verificada contra a `public_key` do publisher.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase17_ed25519_signature.py -q
"""
from __future__ import annotations

import pytest

from app.module_trust.signature import (
    Ed25519SignatureProvider,
    SignatureStatus,
    canonical_manifest_bytes,
    generate_ed25519_keypair,
)

pytestmark = pytest.mark.unit


def test_generate_keypair_returns_pem_bytes():
    private_pem, public_pem = generate_ed25519_keypair()
    assert private_pem.startswith(b"-----BEGIN PRIVATE KEY-----")
    assert public_pem.startswith(b"-----BEGIN PUBLIC KEY-----")


def test_valid_signature_verifies():
    private_pem, public_pem = generate_ed25519_keypair()
    provider = Ed25519SignatureProvider()
    data = b"module content that the publisher vouches for"

    signature = provider.sign(data, private_pem)
    status = provider.verify(data, signature, public_pem.decode())

    assert status == SignatureStatus.VALID


def test_tampered_data_is_invalid():
    private_pem, public_pem = generate_ed25519_keypair()
    provider = Ed25519SignatureProvider()

    signature = provider.sign(b"original content", private_pem)
    status = provider.verify(b"tampered content", signature, public_pem.decode())

    assert status == SignatureStatus.INVALID


def test_wrong_public_key_is_invalid():
    _, attacker_public_pem = generate_ed25519_keypair()
    real_private_pem, _ = generate_ed25519_keypair()
    provider = Ed25519SignatureProvider()

    signature = provider.sign(b"data", real_private_pem)
    status = provider.verify(b"data", signature, attacker_public_pem.decode())

    assert status == SignatureStatus.INVALID


def test_missing_signature_is_not_configured():
    _, public_pem = generate_ed25519_keypair()
    provider = Ed25519SignatureProvider()

    status = provider.verify(b"data", None, public_pem.decode())

    assert status == SignatureStatus.NOT_CONFIGURED


def test_missing_public_key_is_not_configured():
    private_pem, _ = generate_ed25519_keypair()
    provider = Ed25519SignatureProvider()
    signature = provider.sign(b"data", private_pem)

    status = provider.verify(b"data", signature, None)

    assert status == SignatureStatus.NOT_CONFIGURED


def test_malformed_public_key_is_unsupported():
    private_pem, _ = generate_ed25519_keypair()
    provider = Ed25519SignatureProvider()
    signature = provider.sign(b"data", private_pem)

    status = provider.verify(b"data", signature, "not a real PEM key")

    assert status == SignatureStatus.UNSUPPORTED


def test_identify_algorithm():
    assert Ed25519SignatureProvider().identify_algorithm() == "ed25519"


def test_canonical_manifest_bytes_excludes_signature_field():
    raw = {"id": "mod", "version": "1.0.0", "signature": "abc123"}
    without_sig = {"id": "mod", "version": "1.0.0"}

    assert canonical_manifest_bytes(raw) == canonical_manifest_bytes(without_sig)


def test_canonical_manifest_bytes_is_deterministic_regardless_of_key_order():
    raw_a = {"id": "mod", "version": "1.0.0"}
    raw_b = {"version": "1.0.0", "id": "mod"}

    assert canonical_manifest_bytes(raw_a) == canonical_manifest_bytes(raw_b)


def test_canonical_manifest_bytes_changes_when_content_changes():
    raw_a = {"id": "mod", "version": "1.0.0"}
    raw_b = {"id": "mod", "version": "1.0.1"}

    assert canonical_manifest_bytes(raw_a) != canonical_manifest_bytes(raw_b)
