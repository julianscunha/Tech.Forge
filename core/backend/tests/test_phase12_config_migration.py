"""Fase 12 Slice 9 — Config migration no update de módulo (spec §13/§15).

Hook opcional `migrate_config(old_version, old_config) -> new_config`,
declarado pelo módulo (mesmo padrão de `enable`/`disable`/`health_check`,
Fase 9). Diferente daqueles (best-effort), uma falha aqui reaproveita o
rollback de arquivos que `PackageManager.update()` já faz para qualquer
exceção — a spec exige não deixar dados incompatíveis silenciosamente.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_config_migration.py -q
"""
from __future__ import annotations

import asyncio
import json
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))
sys.path.insert(0, str(Path(__file__).parent))

from test_phase4 import make_package_manager

from app.package_manager.enums import UpdateStatus

pytestmark = pytest.mark.integration

MANIFEST_V1 = {
    "id": "cfg_mig_pkg",
    "name": "Cfg Migration Pkg",
    "version": "1.0.0",
    "platform_min_version": "1.0.0",
    "platform_max_version": "2.0.0",
    "category": "Test",
    "vendor": "TechForge",
    "author": "Tester",
    "description": "A test package.",
    "entry_backend": "backend/main.py",
    "entry_frontend": "frontend/index.tsx",
    "icon": "shield-check",
    "order": 10,
    "configuration": {"fields": [{"id": "region", "type": "string", "default": "us-east"}]},
}


def _make_mod_with_backend(tmp: Path, manifest: dict, backend_code: str) -> Path:
    mod_dir = tmp / "src" / manifest["id"]
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "frontend").mkdir(parents=True)
    (mod_dir / "backend" / "main.py").write_text(backend_code, encoding="utf-8")
    (mod_dir / "frontend" / "index.tsx").write_text(
        "export const moduleConfig={}\nexport default function P(){return null}\n"
    )
    (mod_dir / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")

    mod_path = tmp / f"{manifest['id']}-{manifest['version']}.mod"
    with zipfile.ZipFile(mod_path, "w") as zf:
        for f in mod_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(mod_dir))
        zf.writestr("META-INF/TECHFORGE", "TECHFORGE_MODULE_FORMAT=1.0\n")
        zf.writestr("META-INF/BUILD", json.dumps({
            "module_id": manifest["id"], "version": manifest["version"], "format": "techforge-mod-v1",
        }))
    return mod_path


_BACKEND_NO_HOOK = "from fastapi import APIRouter\nrouter=APIRouter()\n"

_BACKEND_WITH_MIGRATE = """
from fastapi import APIRouter
router = APIRouter()

class _Module:
    def migrate_config(self, old_version, old_config):
        # Simula um rename de campo (region -> regions) entre versões —
        # tipo lista não é suportado pelo schema de configuração (Slice 3
        # só cobre string/integer/float/boolean); mantido string aqui.
        return {"regions": old_config.get("region", "us-east")}

module = _Module()
"""

_BACKEND_MIGRATE_RAISES = """
from fastapi import APIRouter
router = APIRouter()

class _Module:
    def migrate_config(self, old_version, old_config):
        raise RuntimeError("boom")

module = _Module()
"""

_BACKEND_MIGRATE_RETURNS_INVALID_TYPE = """
from fastapi import APIRouter
router = APIRouter()

class _Module:
    def migrate_config(self, old_version, old_config):
        return {"regions": 12345}  # deveria ser lista, dispara ConfigValidationError

module = _Module()
"""


async def _get_saved_config(module_id: str, fields):
    from app.db.database import AsyncSessionLocal
    from app.services.module_configuration import get_config
    async with AsyncSessionLocal() as db:
        return await get_config(db, module_id, fields)


async def _delete_config_row(module_id: str):
    from app.db.database import AsyncSessionLocal
    from app.models.module_configuration import ModuleConfiguration
    async with AsyncSessionLocal() as db:
        row = await db.get(ModuleConfiguration, module_id)
        if row is not None:
            await db.delete(row)
            await db.commit()


@pytest.fixture(autouse=True)
def _clean_db_config():
    asyncio.run(_delete_config_row("cfg_mig_pkg"))
    yield
    asyncio.run(_delete_config_row("cfg_mig_pkg"))


def test_update_without_migrate_config_hook_succeeds_normally(tmp_path):
    pm = make_package_manager(tmp_path)
    v1 = _make_mod_with_backend(tmp_path / "v1", MANIFEST_V1.copy(), _BACKEND_NO_HOOK)
    asyncio.run(pm.install(v1))

    v2 = _make_mod_with_backend(tmp_path / "v2", {**MANIFEST_V1, "version": "2.0.0"}, _BACKEND_NO_HOOK)
    result = asyncio.run(pm.update("cfg_mig_pkg", v2))
    assert result.success, result.message


def test_migrate_config_hook_runs_and_persists_new_config(tmp_path):
    from app.module_engine.manifest import ConfigField

    pm = make_package_manager(tmp_path)
    v1 = _make_mod_with_backend(tmp_path / "v1", MANIFEST_V1.copy(), _BACKEND_NO_HOOK)
    asyncio.run(pm.install(v1))

    manifest_v2 = {**MANIFEST_V1, "version": "2.0.0",
                   "configuration": {"fields": [{"id": "regions", "type": "string", "default": ""}]}}
    v2 = _make_mod_with_backend(tmp_path / "v2", manifest_v2, _BACKEND_WITH_MIGRATE)
    result = asyncio.run(pm.update("cfg_mig_pkg", v2))
    assert result.success, result.message

    new_fields = [ConfigField(id="regions", type="string", default="")]
    saved = asyncio.run(_get_saved_config("cfg_mig_pkg", new_fields))
    assert saved == {"regions": "us-east"}


def test_migrate_config_hook_failure_rolls_back_update(tmp_path):
    pm = make_package_manager(tmp_path)
    v1 = _make_mod_with_backend(tmp_path / "v1", MANIFEST_V1.copy(), _BACKEND_NO_HOOK)
    asyncio.run(pm.install(v1))

    v2 = _make_mod_with_backend(
        tmp_path / "v2", {**MANIFEST_V1, "version": "2.0.0"}, _BACKEND_MIGRATE_RAISES
    )
    result = asyncio.run(pm.update("cfg_mig_pkg", v2))
    assert not result.success
    assert result.status == UpdateStatus.FAILED

    # Rollback: versão instalada continua sendo a 1.0.0.
    manifest_path = tmp_path / "installed" / "cfg_mig_pkg" / "manifest.yaml"
    installed_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert installed_manifest["version"] == "1.0.0"


def test_migrate_config_hook_invalid_return_value_rolls_back_update(tmp_path):
    pm = make_package_manager(tmp_path)
    v1 = _make_mod_with_backend(tmp_path / "v1", MANIFEST_V1.copy(), _BACKEND_NO_HOOK)
    asyncio.run(pm.install(v1))

    manifest_v2 = {**MANIFEST_V1, "version": "2.0.0",
                   "configuration": {"fields": [{"id": "regions", "type": "string", "default": ""}]}}
    v2 = _make_mod_with_backend(tmp_path / "v2", manifest_v2, _BACKEND_MIGRATE_RETURNS_INVALID_TYPE)
    result = asyncio.run(pm.update("cfg_mig_pkg", v2))
    assert not result.success

    manifest_path = tmp_path / "installed" / "cfg_mig_pkg" / "manifest.yaml"
    installed_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert installed_manifest["version"] == "1.0.0"
