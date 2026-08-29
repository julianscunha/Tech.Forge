"""Redação de segredos em log — Fase 12 §28.

Nenhum valor gravado via SecretStore deve aparecer em texto puro num log,
mesmo que algum código (do Core ou de um módulo) acidentalmente inclua o
valor numa mensagem.
"""
from __future__ import annotations

import logging

from app.security.secret_store import _known_secret_values

_REDACTED = "***REDACTED***"


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if _known_secret_values:
            message = record.getMessage()
            redacted = message
            for secret_value in _known_secret_values:
                if secret_value and secret_value in redacted:
                    redacted = redacted.replace(secret_value, _REDACTED)
            if redacted != message:
                record.msg = redacted
                record.args = ()
        return True
