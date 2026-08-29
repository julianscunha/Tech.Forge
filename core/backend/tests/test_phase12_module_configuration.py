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
async def test_module_execution_context_build_populates_configuration_from_persisted_values():
    """Regressão: ModuleExecutionContext.configuration ficava sempre {}
    (stub da Fase 9, nunca conectado). Fase 12 §6 exige que o módulo
    consiga acessar sua própria config persistida via o contexto."""
    from datetime import datetime

    from fastapi.testclient import TestClient

    from app.main import app
    from app.module_engine.enums import ModuleStatus
    from app.module_engine.registry import ModuleEntry, registry
    from app.module_runtime.context import ModuleExecutionContext

    module_id = "ctx_config_test"
    manifest_raw = {
        "configuration": {"fields": [{"id": "retention_days", "type": "integer", "default": 30}]},
    }
    entry = ModuleEntry(
        module_id=module_id, name="Ctx Config Test", version="1.0.0",
        category="C", vendor="V", author="A", description="D",
        status=ModuleStatus.INSTALLED, install_date=datetime.now(),
        manifest_raw=manifest_raw,
    )
    try:
        # Registra DEPOIS de entrar no TestClient — o lifespan de startup
        # roda scan_installed() e reconstrói o registry, o que apagaria
        # um registro feito antes.
        with TestClient(app) as client:
            registry.register(entry)
            client.put(f"/api/v1/modules/{module_id}/config", json={"values": {"retention_days": 99}})
            ctx = await ModuleExecutionContext.build(module_id, registry)
        assert ctx is not None
        assert ctx.configuration == {"retention_days": 99}
    finally:
        registry.deregister(module_id)
        from app.db.database import AsyncSessionLocal
        from app.models.module_configuration import ModuleConfiguration
        async with AsyncSessionLocal() as db:
            row = await db.get(ModuleConfiguration, module_id)
            if row is not None:
                await db.delete(row)
                await db.commit()


@pytest.mark.asyncio
async def test_save_config_never_persists_invalid_values(db_session):
    with pytest.raises(ConfigValidationError):
        await save_config(db_session, "mod_b", FIELDS, {"retention_days": "bad"})

    loaded = await get_config(db_session, "mod_b", FIELDS)
    # Nenhuma linha foi gravada — get_config cai nos defaults.
    assert loaded == {"retention_days": 30, "enabled": True}
