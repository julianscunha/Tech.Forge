"""
Signature Provider — Fase 10 §11/§12, Ed25519 real na Fase 17 §7/§12
========================================================================
Arquitetura preparada para assinatura digital, desacoplada do Package
Manager (spec §11: "não acoplar a primeira implementação a todo o
Core"). `NoOpSignatureProvider` (Fase 10) nunca falsifica um resultado
positivo. `Ed25519SignatureProvider` (Fase 17) é o default real: sem
PKI corporativa — o publisher gera o par de chaves localmente (fora do
Core), a chave pública vai pro campo `public_key` do Publisher
Registry, a chave privada nunca toca o Runtime (spec §12).
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
    load_pem_public_key,
)


class SignatureStatus(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    VALID          = "VALID"
    INVALID        = "INVALID"
    UNSUPPORTED    = "UNSUPPORTED"


class SignatureProvider(ABC):
    """
    Interface estável de assinatura — qualquer implementação futura
    (Ed25519 ou outra) implementa isto sem o Package Manager precisar
    saber qual algoritmo está por trás.
    """

    @abstractmethod
    def sign(self, data: bytes, private_key: bytes) -> bytes:
        """Assina `data` com a chave privada. A chave privada NUNCA deve
        ser embutida em um módulo (spec §12) — quem chama isto é
        responsabilidade de quem possui a chave, não o Core."""

    @abstractmethod
    def verify(self, data: bytes, signature: Optional[bytes],
               public_key: Optional[str]) -> SignatureStatus:
        """Verifica `signature` contra `data` usando `public_key`. Nunca
        precisa de acesso à chave privada (spec §12)."""

    @abstractmethod
    def identify_algorithm(self) -> str:
        """Nome do algoritmo usado por esta implementação (ex: 'ed25519')."""


class NoOpSignatureProvider(SignatureProvider):
    """
    Implementação default enquanto não há assinatura real (decisão da
    Fase 10). Nunca finge validar uma assinatura que não pode verificar.
    """

    def sign(self, data: bytes, private_key: bytes) -> bytes:
        raise NotImplementedError(
            "Signing is not implemented in this phase — SignatureProvider "
            "is abstraction-only (Fase 10 decision, see tasks/phase10-plan.md)."
        )

    def verify(self, data: bytes, signature: Optional[bytes],
               public_key: Optional[str]) -> SignatureStatus:
        if signature is None:
            return SignatureStatus.NOT_CONFIGURED
        return SignatureStatus.UNSUPPORTED

    def identify_algorithm(self) -> str:
        return "none"


class Ed25519SignatureProvider(SignatureProvider):
    """
    Assinatura real via Ed25519 (spec §7/§12) — sem PKI corporativa,
    sem HSM obrigatório. `private_key`/`public_key` são PEM (o formato
    já padrão da lib `cryptography`, gerado por `generate_ed25519_keypair`).
    """

    def sign(self, data: bytes, private_key: bytes) -> bytes:
        key = load_pem_private_key(private_key, password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise ValueError("private_key must be an Ed25519 PEM-encoded key")
        return key.sign(data)

    def verify(self, data: bytes, signature: Optional[bytes],
               public_key: Optional[str]) -> SignatureStatus:
        if public_key is None or signature is None:
            return SignatureStatus.NOT_CONFIGURED

        try:
            key = load_pem_public_key(public_key.encode())
        except (ValueError, UnsupportedAlgorithm):
            return SignatureStatus.UNSUPPORTED
        if not isinstance(key, Ed25519PublicKey):
            return SignatureStatus.UNSUPPORTED

        try:
            key.verify(signature, data)
            return SignatureStatus.VALID
        except InvalidSignature:
            return SignatureStatus.INVALID

    def identify_algorithm(self) -> str:
        return "ed25519"


def generate_ed25519_keypair() -> tuple[bytes, bytes]:
    """Gera um par de chaves Ed25519. Retorna (private_key_pem, public_key_pem).

    Conveniência para `techforge trust generate-keypair` — a chave
    privada nunca deve ser commitada nem enviada ao Core (spec §12)."""
    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def canonical_manifest_bytes(raw: dict) -> bytes:
    """Bytes canônicos e determinísticos de um manifest para assinar/verificar.

    Exclui o próprio campo `signature` (senão seria circular: o
    manifest mudaria ao receber a assinatura, invalidando-a). JSON com
    `sort_keys=True` — mesmo dict, mesmos bytes, independente da ordem
    de declaração no YAML.
    """
    payload = {k: v for k, v in raw.items() if k != "signature"}
    return json.dumps(payload, sort_keys=True, default=str).encode("utf-8")


default_signature_provider = Ed25519SignatureProvider()
