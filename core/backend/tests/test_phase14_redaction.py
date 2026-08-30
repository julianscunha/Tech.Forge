"""
TechForge Fase 14 Slice 3 — Redação por padrão de chave
==========================================================
Generaliza SecretRedactionFilter (Fase 12 §28, só valor conhecido) para
também mascarar por nome de campo sensível, mesmo que o valor nunca
tenha sido registrado no SecretStore (spec §8: "não depender apenas da
disciplina do desenvolvedor").
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.security.redaction import SecretRedactionFilter

pytestmark = pytest.mark.unit


def make_record(msg: str) -> logging.LogRecord:
    return logging.LogRecord(name="test", level=logging.INFO, pathname=__file__,
                              lineno=1, msg=msg, args=(), exc_info=None)


class TestKeyPatternRedaction:

    @pytest.mark.parametrize("msg,should_contain", [
        ("connecting with password=hunter2", "password=***REDACTED***"),
        ("API_KEY=sk-abc123xyz sent", "API_KEY=***REDACTED***"),
        ('payload: {"token": "abc123"}', '"token": "***REDACTED***"'),
        ("secret: my-secret-value", "secret: ***REDACTED***"),
        ("private_key=-----BEGIN", "private_key=***REDACTED***"),
        ("credential=abc123", "credential=***REDACTED***"),
    ])
    def test_redacts_sensitive_key_value_pairs(self, msg, should_contain):
        record = make_record(msg)
        SecretRedactionFilter().filter(record)
        assert should_contain in record.getMessage()

    def test_does_not_redact_unrelated_keys(self):
        record = make_record("username=joe status=active")
        SecretRedactionFilter().filter(record)
        assert record.getMessage() == "username=joe status=active"

    def test_never_leaks_the_actual_value(self):
        record = make_record("password=hunter2")
        SecretRedactionFilter().filter(record)
        assert "hunter2" not in record.getMessage()

    def test_still_redacts_known_secret_values(self, monkeypatch):
        from app.security import redaction as redaction_module
        monkeypatch.setattr(redaction_module, "_known_secret_values", {"a-known-value"})
        record = make_record("using a-known-value for the connection")
        SecretRedactionFilter().filter(record)
        assert "a-known-value" not in record.getMessage()
        assert "***REDACTED***" in record.getMessage()
