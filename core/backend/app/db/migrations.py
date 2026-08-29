"""Migrations runner — Fase 12 §14.

Fina camada sobre o Alembic (já em requirements.txt, nunca usado antes desta
fase) — substitui a whitelist ad-hoc que existia em `app.db.database._migrate`.
Roda em thread separada (`upgrade_head`/`current_revision` são síncronas —
Alembic internamente faz `asyncio.run()` em `alembic/env.py`, que não pode
ser chamado de dentro de um event loop já rodando).
"""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

_ALEMBIC_DIR = Path(__file__).resolve().parents[2] / "alembic"
_ALEMBIC_INI = _ALEMBIC_DIR.parent / "alembic.ini"


def _config(database_url: str | None = None) -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_ALEMBIC_DIR))
    if database_url:
        cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def upgrade_head(database_url: str | None = None) -> None:
    command.upgrade(_config(database_url), "head")


def head_revision() -> str | None:
    script = ScriptDirectory.from_config(_config())
    return script.get_current_head()
