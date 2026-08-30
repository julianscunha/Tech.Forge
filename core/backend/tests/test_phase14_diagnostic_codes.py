"""
TechForge Fase 14 Slice 11 — Diagnostic Codes
================================================
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.db.database import Base
from app.observability.diagnostic_codes import resolve_diagnostic_code
from app.services.error_registry import ErrorRegistryService

pytestmark = pytest.mark.unit


class TestResolveDiagnosticCode:

    @pytest.mark.parametrize("source,expected_code", [
        ("execution", "TF-EXECUTION-001"),
        ("dependency", "TF-DEPENDENCY-001"),
        ("runtime", "TF-RUNTIME-001"),
    ])
    def test_known_sources_resolve_to_stable_code(self, source, expected_code):
        diagnostic = resolve_diagnostic_code(source)
        assert diagnostic is not None
        assert diagnostic.code == expected_code
        assert diagnostic.title

    def test_unknown_source_resolves_to_none(self):
        assert resolve_diagnostic_code("something_made_up") is None


@pytest_asyncio.fixture()
async def db_session(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'codes.db').as_posix()}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest.mark.integration
class TestErrorRegistryAttachesCode:

    @pytest.mark.asyncio
    async def test_record_attaches_known_code(self, db_session):
        entry = await ErrorRegistryService.record(db_session, source="execution", message="boom")
        assert entry.code == "TF-EXECUTION-001"

    @pytest.mark.asyncio
    async def test_record_leaves_code_none_for_unknown_source(self, db_session):
        entry = await ErrorRegistryService.record(db_session, source="something_else", message="x")
        assert entry.code is None
