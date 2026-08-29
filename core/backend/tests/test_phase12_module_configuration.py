"""Fase 12 Slice 3 (parte 2) — validação + persistência de module config.

Spec §12: config inválida nunca persiste. Validação tipada via schema
dinâmico (pydantic.create_model) sobre os campos declarados no manifest.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_module_configuration.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.db.database import Base
from app.models.module_configuration import ModuleConfiguration  # noqa: F401 — registra a tabela
from app.module_engine.manifest import ConfigField
from app.services.module_configuration import ConfigValidationError, get_config, save_config, validate_config

FIELDS = [
    ConfigField(id="retention_days", type="integer", default=30),
    ConfigField(id="enabled", type="boolean", default=True),
]


@pytest_asyncio.fixture()
async def db_session(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'cfg.db').as_posix()}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


def test_validate_config_applies_defaults_for_missing_fields():
    result = validate_config(FIELDS, {})
    assert result == {"retention_days": 30, "enabled": True}


def test_validate_config_accepts_valid_override():
    result = validate_config(FIELDS, {"retention_days": 90})
    assert result["retention_days"] == 90


def test_validate_config_rejects_wrong_type():
    with pytest.raises(ConfigValidationError):
        validate_config(FIELDS, {"retention_days": "not a number"})


def test_validate_config_rejects_unknown_key():
    with pytest.raises(ConfigValidationError):
        validate_config(FIELDS, {"nope": 1})


@pytest.mark.asyncio
async def test_save_and_get_config_round_trips(db_session):
    saved = await save_config(db_session, "mod_a", FIELDS, {"retention_days": 7})
    assert saved["retention_days"] == 7

    loaded = await get_config(db_session, "mod_a", FIELDS)
    assert loaded == saved


@pytest.mark.asyncio
async def test_save_config_never_persists_invalid_values(db_session):
    with pytest.raises(ConfigValidationError):
        await save_config(db_session, "mod_b", FIELDS, {"retention_days": "bad"})

    loaded = await get_config(db_session, "mod_b", FIELDS)
    # Nenhuma linha foi gravada — get_config cai nos defaults.
    assert loaded == {"retention_days": 30, "enabled": True}
