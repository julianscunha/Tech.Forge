"""
Trust Level — Fase 10 §8
============================
Nível de confiança calculado de UM módulo — combina integridade dos
arquivos, identidade do publisher e status de assinatura. Substitui o
antigo `TrustLevel` de `package_manager/enums.py` (Fase 4, minusculo, nunca
era calculado de verdade (sempre hardcoded UNSIGNED) e tinha valores
diferentes dos desta spec.

Não confundir com `PublisherTrustStatus` (module_trust/publisher.py) —
aquele é o status administrativo DO PUBLISHER (confiamos nele em
geral?); este é o resultado calculado PARA UM MÓDULO específico.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from app.module_trust.integrity import IntegrityStatus
from app.module_trust.publisher import PublisherTrustStatus


class TrustLevel(str, Enum):
    TRUSTED    = "TRUSTED"
    VERIFIED   = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    MODIFIED   = "MODIFIED"
    INVALID    = "INVALID"


class TrustResolver:
    """
    Regras de resolução (spec §8, decisão de implementação já tomada):

        INVALID_MANIFEST / MISSING_FILE (integridade)  -> INVALID
        publisher.trust_status == REVOKED              -> INVALID
        MODIFIED / UNEXPECTED_FILE (integridade)        -> MODIFIED
            (decisão: um arquivo não declarado também conta como
            conteúdo alterado em relação ao que foi registrado —
            mesmo tratamento de MODIFIED, não é inofensivo)
        integridade VALID + publisher desconhecido       -> UNVERIFIED
        integridade VALID + publisher conhecido, não revogado,
            signature_status == VALID e publisher TRUSTED -> TRUSTED
        integridade VALID + publisher conhecido, não revogado,
            caso contrário                               -> VERIFIED

    TRUSTED é estruturalmente inalcançável nesta fase — não existe
    assinatura real (Slice 4 é só abstração, sempre NOT_CONFIGURED).
    Isso é esperado, não um bug.
    """

    @staticmethod
    def resolve(integrity_status: IntegrityStatus, publisher: Optional[object],
                signature_status: str = "NOT_CONFIGURED") -> TrustLevel:
        if integrity_status in (IntegrityStatus.INVALID_MANIFEST, IntegrityStatus.MISSING_FILE):
            return TrustLevel.INVALID

        if publisher is not None and getattr(publisher, "trust_status", None) == PublisherTrustStatus.REVOKED.value:
            return TrustLevel.INVALID

        if integrity_status in (IntegrityStatus.MODIFIED, IntegrityStatus.UNEXPECTED_FILE):
            return TrustLevel.MODIFIED

        # A partir daqui, integrity_status == VALID
        if publisher is None:
            return TrustLevel.UNVERIFIED

        if (signature_status == "VALID"
                and getattr(publisher, "trust_status", None) == PublisherTrustStatus.TRUSTED.value):
            return TrustLevel.TRUSTED

        return TrustLevel.VERIFIED
