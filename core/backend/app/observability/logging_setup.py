"""Logger central — Fase 14 §4/§5/§7.

Console: formato humano (como já era). Arquivo (`logs/backend.jsonl`):
JSON-lines, uma linha por registro, parseável por qualquer ferramenta
externa (jq, log viewer, etc.) sem depender de um formato proprietário.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.observability.context import get_log_context

_HUMAN_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


class LogContextFilter(logging.Filter):
    """Anexa o contexto de log atual (contextvars) ao record, pra qualquer
    Formatter — JSON ou humano — poder usá-lo."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.log_context = get_log_context()
        return True


class JsonLogFormatter(logging.Formatter):
    """Uma linha JSON por registro. Campos de contexto ausentes são
    omitidos (spec §6: 'não obrigar todos os campos em todos os logs')."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }
        payload.update(getattr(record, "log_context", {}))
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_DEFAULT_MAX_BYTES = 10_000_000  # 10MB
_DEFAULT_BACKUP_COUNT = 5


def configure_logging(level: str = "INFO", logs_path: Path | None = None,
                       file_level: str | None = None,
                       max_bytes: int = _DEFAULT_MAX_BYTES,
                       backup_count: int = _DEFAULT_BACKUP_COUNT) -> None:
    """Configura o root logger: console humano + arquivo JSON-lines.

    `level` e `file_level` podem divergir (ex: console em WARNING pra não
    poluir o terminal, arquivo em DEBUG pra investigação posterior).
    `file_level` usa `level` como default. O root logger precisa aceitar o
    nível mais permissivo dos dois, senão os records nem chegam nos handlers.

    Substitui `logging.basicConfig` — chamar uma vez no startup do app.
    """
    file_level = file_level or level
    root = logging.getLogger()
    root.setLevel(min(logging.getLevelName(level), logging.getLevelName(file_level)))
    root.handlers.clear()

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(_HUMAN_FORMAT))
    console.addFilter(LogContextFilter())
    root.addHandler(console)

    if logs_path is not None:
        logs_path.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(logs_path / "backend.jsonl", encoding="utf-8",
                                            maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(JsonLogFormatter())
        file_handler.addFilter(LogContextFilter())
        root.addHandler(file_handler)
