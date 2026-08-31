"""
Security Policy — Fase 17 §40/§41
=====================================
Formaliza a política já em vigor implicitamente (Desktop nunca bloqueia
instalação por Trust Level sozinho — só avisa; o bloqueio real vem de
integridade/limites de recursos, ver `archive_safety.py`) numa
abstração que pode evoluir por ambiente, sem hardcodar o comportamento
definitivo espalhado pelo código.

Mesmo racional do `SignatureProvider` da Fase 10: a interface é real,
a implementação Server é preparação documentada — não hipotética
(mesmo princípio da Fase 13 adiada: não construir Server especulativo
sem caso de uso real).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.module_trust.trust import TrustLevel


class SecurityPolicy(ABC):
    """Decide, por ambiente, se um Trust Level bloqueia a instalação e se
    merece aviso. Nunca decide sozinha o Trust Level em si (isso é
    `TrustResolver`) — só o que fazer com o resultado."""

    @abstractmethod
    def allows_install(self, trust_level: TrustLevel) -> bool:
        """True se a instalação pode prosseguir com este Trust Level."""

    @abstractmethod
    def requires_warning(self, trust_level: TrustLevel) -> bool:
        """True se este Trust Level merece aviso ao usuário/log."""


class DesktopSecurityPolicy(SecurityPolicy):
    """Política em vigor desde a Fase 10 (nunca antes formalizada): local
    trust, developer flexibility, cofre de segredos do SO. Nunca bloqueia
    por Trust Level isolado — um módulo de desenvolvimento local
    (UNVERIFIED) é o caso comum, não uma ameaça."""

    def allows_install(self, trust_level: TrustLevel) -> bool:
        return True

    def requires_warning(self, trust_level: TrustLevel) -> bool:
        return trust_level != TrustLevel.TRUSTED and trust_level != TrustLevel.VERIFIED


class ServerSecurityPolicy(SecurityPolicy):
    """Server futuro (central policy, multi-user, trust/secrets
    centralizados) — não implementada nesta fase. Levanta
    `NotImplementedError` deliberadamente em vez de fingir uma política
    que ninguém validou (mesmo padrão do `NoOpSignatureProvider` original
    da Fase 10)."""

    def allows_install(self, trust_level: TrustLevel) -> bool:
        raise NotImplementedError(
            "ServerSecurityPolicy is not implemented — Server is a future "
            "phase (see Fase 13, adiada). SecurityPolicy is abstraction-only "
            "for this environment."
        )

    def requires_warning(self, trust_level: TrustLevel) -> bool:
        raise NotImplementedError(
            "ServerSecurityPolicy is not implemented — Server is a future "
            "phase (see Fase 13, adiada). SecurityPolicy is abstraction-only "
            "for this environment."
        )


default_security_policy: SecurityPolicy = DesktopSecurityPolicy()
