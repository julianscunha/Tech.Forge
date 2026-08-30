"""Fase 15 Slice 13 — E2E crítico (spec §12).

Fluxo: Install → Validate (implícito no install) → Activate (já ativo por
default) → Execute (runtime status) → Deactivate → Remove — usando um .mod
REAL construído em disco, não um ModuleEntry registrado manualmente (que é
o que os testes de runtime/lifecycle existentes fazem). Nenhum teste atual
encadeia os 7 passos numa sequência só — este prova que as costuras entre
Package Manager (Fase 4), Registry (Fase 2) e Runtime (Fase 9) realmente
se conectam de ponta a ponta.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_e2e_module_lifecycle.py -q
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.main import app  # noqa: E402
from app.module_engine.enums import ModuleStatus  # noqa: E402
from app.module_engine.registry import registry  # noqa: E402

pytestmark = pytest.mark.e2e

MANIFEST = {
    "id": "e2e_flow_mod",
    "name": "E2E Flow Module",
    "version": "1.0.0",
    "platform_min_version": "1.0.0",
    "platform_max_version": "2.0.0",
    "category": "Test",
    "vendor": "TechForge",
    "author": "Tester",
    "description": "Módulo real construído em disco pra provar o fluxo e2e completo.",
    "entry_backend": "backend/main.py",
    "entry_frontend": "frontend/index.tsx",
    "icon": "boxes",
    "order": 1,
}


def _build_mod_file(tmp_path: Path) -> Path:
    mod_dir = tmp_path / "src" / MANIFEST["id"]
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "frontend").mkdir(parents=True)
    (mod_dir / "backend" / "main.py").write_text(
        "from fastapi import APIRouter\nrouter = APIRouter()\n", encoding="utf-8"
    )
    (mod_dir / "frontend" / "index.tsx").write_text(
        "export default function P(){return null}\n", encoding="utf-8"
    )
    (mod_dir / "manifest.yaml").write_text(yaml.dump(MANIFEST), encoding="utf-8")

    mod_path = tmp_path / f"{MANIFEST['id']}-{MANIFEST['version']}.mod"
    with zipfile.ZipFile(mod_path, "w") as zf:
        for f in mod_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(mod_dir))
        zf.writestr("META-INF/TECHFORGE", "TECHFORGE_MODULE_FORMAT=1.0\n")
        zf.writestr("META-INF/BUILD", json.dumps({"module_id": MANIFEST["id"], "version": MANIFEST["version"]}))
    return mod_path


@pytest.fixture()
def package_manager(tmp_path, monkeypatch):
    from app.core.settings import settings
    from app.package_manager.manager import PackageManager
    from app.package_manager.repository import LocalRepositoryProvider

    installed = tmp_path / "installed"
    cache = tmp_path / "cache"
    repo_path = tmp_path / "repository"
    for d in (installed, cache, repo_path):
        d.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", installed)

    return PackageManager(
        installed_path=installed,
        cache_path=cache,
        repository=LocalRepositoryProvider(repository_path=repo_path, cache_path=cache),
        use_global_registry=True,  # precisa ser visível pro TestClient/registry global
    )


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.asyncio
async def test_full_module_lifecycle_install_to_remove(package_manager, client, tmp_path):
    module_id = MANIFEST["id"]
    mod_path = _build_mod_file(tmp_path)

    try:
        # 1. Install — Package Manager escreve em disco + hot-reload do registry global
        install_result = await package_manager.install(mod_path)
        assert install_result.success, install_result.message

        # 2. Validate (implícito) — registry só marca INSTALLED se manifest/compat passaram
        entry = registry.get(module_id)
        assert entry is not None
        assert entry.status == ModuleStatus.INSTALLED

        # 3. Activate — instalação nova já nasce ativa (INSTALLED), não precisa de activate_module
        # 4. Execute — ação básica sobre o módulo recém-instalado via API (Module Quality, Slice 10)
        response = client.get(f"/api/v1/modules/{module_id}/quality")
        assert response.status_code == 200
        assert response.json()["module_id"] == module_id

        # 5. Deactivate — INSTALLED → DISABLED
        from app.db.database import AsyncSessionLocal
        from app.package_manager.lifecycle import deactivate_module

        async with AsyncSessionLocal() as db:
            deactivate_result = await deactivate_module(db, module_id)
        assert deactivate_result["ok"] is True
        assert registry.get(module_id).status == ModuleStatus.DISABLED

        # 6. Remove — Package Manager apaga do disco + hot-reload
        remove_result = await package_manager.remove(module_id)
        assert remove_result.success, remove_result.message
        assert registry.get(module_id) is None
    finally:
        # limpeza defensiva — não deixar o módulo de teste preso no registry global
        if registry.get(module_id) is not None:
            registry.deregister(module_id)
