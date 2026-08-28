"""
Publisher — Fase 10 §10
===========================
Modelo de identidade de quem publicou um módulo. Separado do TrustLevel
do módulo (Slice 3) — PublisherTrustStatus é o status administrativo do
PUBLISHER (confiamos nele em geral?), TrustLevel é o resultado calculado
para UM módulo específico (integridade + publisher + assinatura).
"""
from __future__ import annotations

from enum import Enum


class PublisherType(str, Enum):
    OFFICIAL          = "OFFICIAL"
    INTERNAL          = "INTERNAL"
    THIRD_PARTY       = "THIRD_PARTY"
    LOCAL_DEVELOPMENT = "LOCAL_DEVELOPMENT"


class PublisherTrustStatus(str, Enum):
    TRUSTED   = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"
    REVOKED   = "REVOKED"
