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
# Fase 17 §25 — "authorization" explícito. Valor entre aspas pode conter
# espaços (delimitado pela aspa de fechamento); valor sem aspas também
# pode ("Authorization: Bearer xxx" tem espaço no meio) — sem isso, o
# padrão antigo parava no primeiro espaço e só "Bearer" era redigido,
# deixando o token de verdade exposto.
_SENSITIVE_KEY_PATTERN = re.compile(
    r'(?i)(?P<qk>["\']?)\b(?P<key>password|passwd|api[_-]?key|token|secret|'
    r'private[_-]?key|credentials?|authorization)\b(?P=qk)'
    r'(?P<sep>\s*[:=]\s*)'
    r'(?:(?P<vq>["\'])(?P<qval>[^"\']+)(?P=vq)|(?P<val>[^"\',}]+))'
)


def _redact_by_key_pattern(message: str) -> str:
    def _replace(m: re.Match) -> str:
        prefix = f"{m.group('qk')}{m.group('key')}{m.group('qk')}{m.group('sep')}"
        if m.group("vq"):
            return f"{prefix}{m.group('vq')}{_REDACTED}{m.group('vq')}"
        return f"{prefix}{_REDACTED}"

    return _SENSITIVE_KEY_PATTERN.sub(_replace, message)


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
