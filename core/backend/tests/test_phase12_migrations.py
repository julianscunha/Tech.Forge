"""Fase 12 Slice 2 — Migrations via Alembic (spec §14).

Substitui a whitelist ad-hoc `app.db.database._migrate()`. Dois cenários
obrigatórios: banco novo (create_all já cria tudo, upgrade não deve
duplicar coluna) e banco legado (tabela `modules` sem source_type/
source_location, como uma instalação anterior à Fase 11).

`migrations.upgrade_head()` é síncrona por natureza (Alembic roda
`asyncio.run()` internamente em alembic/env.py) — chamada aqui fora de
qualquer event loop, como faz o CLI real. `init_db()` (contexto async)
delega pra thread via `asyncio.to_thread`.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_migrations.py -q
"""
from __future__ import annotations
import pytest

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from sqlalchemy import create_engine

import app.api  # noqa: F401 — registra todos os models em Base.metadata (mesma ordem da produção)
from app.db import migrations
from app.db.database import Base

pytestmark = pytest.mark.unit


def _sqlite_url(tmp_path: Path) -> tuple[str, Path]:
    db_file = tmp_path / "test.db"
    return f"sqlite+aiosqlite:///{db_file.as_posix()}", db_file


def _columns(db_file: Path, table: str) -> set[str]:
    conn = sqlite3.connect(str(db_file))
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


def test_upgrade_head_on_fresh_db_created_via_create_all_does_not_duplicate_columns(tmp_path):
    url, db_file = _sqlite_url(tmp_path)
    sync_engine = create_engine(url.replace("+aiosqlite", ""))
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()

    migrations.upgrade_head(database_url=url)  # não deve levantar (coluna já existe)

    columns = _columns(db_file, "modules")
    assert {"source_type", "source_location"}.issubset(columns)


def test_upgrade_head_adds_missing_columns_on_legacy_db(tmp_path):
    url, db_file = _sqlite_url(tmp_path)
    conn = sqlite3.connect(str(db_file))
    # Schema legado: tabela `modules` sem source_type/source_location
    # (como uma instalação anterior à Fase 11).
    conn.execute("CREATE TABLE modules (id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL)")
    conn.commit()
    conn.close()

    migrations.upgrade_head(database_url=url)

    columns = _columns(db_file, "modules")
    assert {"source_type", "source_location"}.issubset(columns)


def test_upgrade_head_is_idempotent(tmp_path):
    url, _ = _sqlite_url(tmp_path)
    sync_engine = create_engine(url.replace("+aiosqlite", ""))
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()

    migrations.upgrade_head(database_url=url)
    migrations.upgrade_head(database_url=url)  # segunda vez não deve levantar
