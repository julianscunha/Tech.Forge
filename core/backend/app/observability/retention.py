"""Log retention — Fase 14 §9.

Retenção configurável por nível (ex: DEBUG 7d / INFO-WARNING 30d / ERROR
90d — valores default do spec, ajustáveis via platform_config). Rodado de
forma síncrona no startup — sem agendador, é overkill pro Desktop.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_RETENTION_DAYS: dict[str, int] = {
    "DEBUG": 7,
    "INFO": 30,
    "WARNING": 30,
    "ERROR": 90,
    "CRITICAL": 90,
}


def cleanup_old_logs(jsonl_path: Path, retention_days: dict[str, int] | None = None) -> int:
    """Remove do arquivo JSON-lines as entradas mais antigas que a retenção
    configurada para o nível delas. Linhas malformadas ou sem nível
    reconhecido na config são mantidas (nunca apaga o que não entende).
    Retorna a quantidade de linhas removidas."""
    if not jsonl_path.exists():
        return 0

    retention_days = retention_days if retention_days is not None else DEFAULT_RETENTION_DAYS
    now = datetime.now(timezone.utc)

    kept_lines: list[str] = []
    removed = 0
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if _is_expired(line, retention_days, now):
            removed += 1
        else:
            kept_lines.append(line)

    if removed:
        jsonl_path.write_text("\n".join(kept_lines) + "\n" if kept_lines else "", encoding="utf-8")
    return removed


def _is_expired(line: str, retention_days: dict[str, int], now: datetime) -> bool:
    try:
        entry = json.loads(line)
        level = entry["level"]
        timestamp = datetime.fromisoformat(entry["timestamp"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return False

    max_days = retention_days.get(level)
    if max_days is None:
        return False
    return (now - timestamp).days > max_days
