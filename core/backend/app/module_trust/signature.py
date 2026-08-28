"""
Signature Provider — Fase 10 §11/§12
========================================
Arquitetura preparada para assinatura digital, desacoplada do Package
Manager (spec §11: "não acoplar a primeira implementação a todo o
Core"). Decisão do usuário: só a abstração nesta fase, sem Ed25519 real
— nenhum módulo hoje tem par de chaves nem caso de uso de assinatura
ponta a ponta. `NoOpSignatureProvider` é a implementação default:
nunca falsifica um resultado positivo, sempre reporta honestamente que
a verificação não está disponível.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


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


default_signature_provider = NoOpSignatureProvider()
