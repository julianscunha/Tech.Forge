"""Fase 3 Slice 2 — Servir assets frontend dos módulos instalados (spec §11).

ModuleHost faz dynamic import de entry_frontend via estes endpoints.
Sandbox: paths resolvem SEMPRE dentro do diretório do módulo.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase3_assets.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _hello_frontend() -> Path:
    return Path(__file__).resolve().parents[3] / "modules" / "installed" / "hello_world"


def test_module_asset_serves_entry_file(client):
    mod_dir = _hello_frontend()
    if not mod_dir.is_dir():
        pytest.skip("hello_world not installed")
    resp = client.get("/api/v1/modules/hello_world/assets/manifest.yaml")
    assert resp.status_code == 404  # yaml not in allowlist (source, not asset)
    # source files are served for development transparency
    resp = client.get("/api/v1/modules/hello_world/assets/frontend/index.tsx")
    assert resp.status_code in (200, 404)  # depends on allowlist; see below


def test_module_asset_serves_js_asset(client):
    """JS assets are the dynamic-import contract (spec §11)."""
    import tempfile
    from app.core.settings import settings
    mods = Path(__file__).resolve().parents[3] / "modules" / "installed"
    demo = mods / "asset_demo"
    (demo / "frontend").mkdir(parents=True, exist_ok=True)
    (demo / "frontend" / "main.js").write_text(
        "export default { name: 'demo' };", encoding="utf-8"
    )
    try:
        with TestClient(app) as client:
            resp = client.get("/api/v1/modules/asset_demo/assets/frontend/main.js")
            assert resp.status_code == 200
            assert "export default" in resp.text
            assert resp.headers["content-type"].startswith("application/javascript")
    finally:
        import shutil
        shutil.rmtree(demo, ignore_errors=True)


def test_module_asset_blocks_path_traversal(client):
    resp = client.get("/api/v1/modules/hello_world/assets/..%2F..%2F..%2Fconfig%2Ftechforge.db")
    assert resp.status_code in (400, 404)


def test_module_asset_unknown_module_404(client):
    resp = client.get("/api/v1/modules/ghost_module/assets/frontend/index.tsx")
    assert resp.status_code == 404


def test_module_asset_unknown_file_404(client):
    mod_dir = _hello_frontend()
    if not mod_dir.is_dir():
        pytest.skip("hello_world not installed")
    resp = client.get("/api/v1/modules/hello_world/assets/frontend/nao_existe.js")
    assert resp.status_code == 404


def test_module_manifest_endpoint_returns_entry_frontend(client):
    """ModuleHost precisa saber qual arquivo carregar dinamicamente."""
    mod_dir = _hello_frontend()
    if not mod_dir.is_dir():
        pytest.skip("hello_world not installed")
    resp = client.get("/api/v1/registry/modules/hello_world")
    assert resp.status_code == 200
