"""Redação de segredos em log — Fase 12 §28.

Nenhum valor gravado via SecretStore deve aparecer em texto puro num log,
mesmo que algum código (do Core ou de um módulo) acidentalmente inclua o
valor numa mensagem.
"""
from __future__ import annotations

import logging
import re

from app.security.secret_store import _known_secret_values

_REDACTED = "***REDACTED***"

# Fase 14 §8 — não depender só de valor conhecido registrado no SecretStore;
# mascarar também por nome de campo sensível, no formato key=value ou
# JSON-style "key": "value". Cobre as chaves citadas literalmente no spec.
_SENSITIVE_KEY_PATTERN = re.compile(
    r'(?i)(["\']?)\b(password|passwd|api[_-]?key|token|secret|private[_-]?key|credentials?)\b\1'
    r'(\s*[:=]\s*)'
    r'(["\']?)([^"\',\s}]+)\4'
)


def _redact_by_key_pattern(message: str) -> str:
    return _SENSITIVE_KEY_PATTERN.sub(
        lambda m: f"{m.group(1)}{m.group(2)}{m.group(1)}{m.group(3)}{m.group(4)}{_REDACTED}{m.group(4)}",
        message,
    )


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = _redact_by_key_pattern(message)
        for secret_value in _known_secret_values:
            if secret_value and secret_value in redacted:
                redacted = redacted.replace(secret_value, _REDACTED)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True
