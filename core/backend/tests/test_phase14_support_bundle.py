"""
TechForge Fase 14 Slice 16 — Support Bundle sanitizado
=========================================================
"""
from __future__ import annotations

import json
import sys
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


class TestSupportBundle:

    @pytest.mark.asyncio
    async def test_build_zip_contains_expected_files(self, client):
        from app.db.database import AsyncSessionLocal
        from app.services.support_bundle import SupportBundleService

        async with AsyncSessionLocal() as db:
            data = await SupportBundleService.build_zip(db)

        zf = zipfile.ZipFile(BytesIO(data))
        names = set(zf.namelist())
        assert "diagnostic_snapshot.json" in names
        assert "platform_config.json" in names
        assert "module_registry.json" in names
        assert "dependency_graph.mmd" in names

    @pytest.mark.asyncio
    async def test_diagnostic_snapshot_is_valid_json(self, client):
        from app.db.database import AsyncSessionLocal
        from app.services.support_bundle import SupportBundleService

        async with AsyncSessionLocal() as db:
            data = await SupportBundleService.build_zip(db)

        zf = zipfile.ZipFile(BytesIO(data))
        snapshot = json.loads(zf.read("diagnostic_snapshot.json"))
        assert "platform_version" in snapshot

    @pytest.mark.asyncio
    async def test_module_registry_lists_installed_modules(self, client):
        from app.db.database import AsyncSessionLocal
        from app.services.support_bundle import SupportBundleService

        async with AsyncSessionLocal() as db:
            data = await SupportBundleService.build_zip(db)

        zf = zipfile.ZipFile(BytesIO(data))
        modules = json.loads(zf.read("module_registry.json"))
        module_ids = [m["module_id"] for m in modules]
        assert "hello_world" in module_ids

    @pytest.mark.asyncio
    async def test_platform_config_never_contains_secret_like_keys(self, client):
        """settings.py nunca guarda segredo (Fase 12 §9) — mesma garantia
        que já vale pra GET /api/v1/config vale aqui, sem redação extra."""
        from app.db.database import AsyncSessionLocal
        from app.services.support_bundle import SupportBundleService

        async with AsyncSessionLocal() as db:
            data = await SupportBundleService.build_zip(db)

        zf = zipfile.ZipFile(BytesIO(data))
        config = json.loads(zf.read("platform_config.json"))
        suspicious = {"password", "secret", "api_key", "private_key", "credential"}
        assert not (suspicious & set(config.keys()))

    @pytest.mark.asyncio
    async def test_bundle_never_includes_module_data_directory(self, client):
        from app.db.database import AsyncSessionLocal
        from app.services.support_bundle import SupportBundleService

        async with AsyncSessionLocal() as db:
            data = await SupportBundleService.build_zip(db)

        zf = zipfile.ZipFile(BytesIO(data))
        assert not any("data/" in name for name in zf.namelist())
