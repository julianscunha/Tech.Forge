"""Fase 17 Slice 9 — SecurityPolicy abstraction (spec §40/§41, critérios 25/26).

Formaliza a política já em vigor implicitamente (Desktop nunca bloqueia
por trust level sozinho, só avisa) numa abstração que pode evoluir por
ambiente sem hardcodar comportamento definitivo em código espalhado —
mesmo racional do `SignatureProvider` da Fase 10 (abstração real,
implementação mínima) e da Fase 13 adiada (Server não é hipotético
até haver caso de uso real).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase17_security_policy.py -q
"""
from __future__ import annotations

import pytest

from app.module_trust.security_policy import (
    DesktopSecurityPolicy,
    SecurityPolicy,
    ServerSecurityPolicy,
    default_security_policy,
)
from app.module_trust.trust import TrustLevel

pytestmark = pytest.mark.unit


def test_cannot_instantiate_abstract_base_directly():
    with pytest.raises(TypeError):
        SecurityPolicy()


class TestDesktopSecurityPolicy:

    @pytest.mark.parametrize("level", list(TrustLevel))
    def test_never_blocks_install_by_trust_level_alone(self, level):
        """Desktop: developer flexibility — bloqueio real é via integridade/
        zip-bomb (Slice 1), não trust level isolado."""
        assert DesktopSecurityPolicy().allows_install(level) is True

    @pytest.mark.parametrize("level,expected", [
        (TrustLevel.TRUSTED, False),
        (TrustLevel.VERIFIED, False),
        (TrustLevel.UNVERIFIED, True),
        (TrustLevel.MODIFIED, True),
        (TrustLevel.INVALID, True),
    ])
    def test_warns_for_unverified_or_worse(self, level, expected):
        assert DesktopSecurityPolicy().requires_warning(level) is expected


class TestServerSecurityPolicy:
    """Não implementada — Server é fase futura, mesmo racional da Fase 13
    adiada. A abstração existe pra quando for necessária, sem fingir uma
    política real que ninguém validou."""

    def test_allows_install_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            ServerSecurityPolicy().allows_install(TrustLevel.VERIFIED)

    def test_requires_warning_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            ServerSecurityPolicy().requires_warning(TrustLevel.VERIFIED)


def test_default_security_policy_is_desktop():
    assert isinstance(default_security_policy, DesktopSecurityPolicy)
