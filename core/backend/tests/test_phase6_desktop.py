"""Fase 6 Slice 1 — Modo Desktop: backend serve frontend estático (spec §10).

SERVE_STATIC_FRONTEND=true + dist/ existente → StaticFiles em / com SPA fallback.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase6_desktop.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

import app.main as main_mod

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

pytestmark = pytest.mark.integration


def test_settings_has_serve_static_flag_default_false():
    from app.core.settings import Settings
    s = Settings()
    assert s.SERVE_STATIC_FRONTEND is False


def test_settings_frontend_dist_path():
    from app.core.settings import settings
    assert hasattr(settings, "FRONTEND_DIST_PATH")
    assert str(settings.FRONTEND_DIST_PATH).endswith("dist")


def test_static_mounted_when_enabled(tmp_path, monkeypatch):
    """Flag on + dist existente → index.html servido na raiz."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>SPA</html>", encoding="utf-8")

    monkeypatch.setattr(main_mod.settings, "SERVE_STATIC_FRONTEND", True)
    monkeypatch.setattr(main_mod.settings, "FRONTEND_DIST_PATH", dist)

    from fastapi import FastAPI

    test_app = FastAPI()
    main_mod._mount_static_frontend(test_app)

    from fastapi.testclient import TestClient
    with TestClient(test_app) as c:
        resp = c.get("/")
        assert resp.status_code == 200
        assert "SPA" in resp.text


def test_no_mount_when_disabled(tmp_path, monkeypatch):
    """Default (flag off) → nenhuma rota de static frontend."""
    dist = tmp_path / "dist"
    dist.mkdir()

    monkeypatch.setattr(main_mod.settings, "SERVE_STATIC_FRONTEND", False)
    monkeypatch.setattr(main_mod.settings, "FRONTEND_DIST_PATH", dist)

    from fastapi import FastAPI

    test_app = FastAPI()
    main_mod._mount_static_frontend(test_app)

    api_paths = [r.path for r in test_app.routes if not str(r.path).startswith("/openapi")]
    assert "/" not in [r.path for r in test_app.routes]


def test_spa_fallback_unknown_route_serves_index(tmp_path, monkeypatch):
    """Rota não-API inexistente no disco → index.html (SPA routing)."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>SPA</html>", encoding="utf-8")

    monkeypatch.setattr(main_mod.settings, "SERVE_STATIC_FRONTEND", True)
    monkeypatch.setattr(main_mod.settings, "FRONTEND_DIST_PATH", dist)

    from fastapi import FastAPI

    test_app = FastAPI()
    main_mod._mount_static_frontend(test_app)

    from fastapi.testclient import TestClient
    client = TestClient(test_app)
    resp = client.get("/some/spa/route")
    assert resp.status_code == 200
    assert "SPA" in resp.text


def test_spa_fallback_does_not_shadow_module_routes_in_desktop_mode(tmp_path, monkeypatch):
    """Regressão real: em modo desktop, NENHUMA rota de módulo respondia —
    _mount_static_frontend() era chamado em create_app() (síncrono, antes
    do app subir), então o catch-all `/{full_path:path}` ficava registrado
    ANTES das rotas de módulo (montadas depois, dentro do lifespan). Starlette
    casa rotas pela ordem de registro, não pela mais específica — então o
    catch-all sempre vencia, e QUALQUER endpoint de módulo (ex: ping de
    hello_world) devolvia 500 (`raise FileNotFoundError` não tratado) em vez
    de rodar de verdade. Fix: _mount_static_frontend() só é chamado dentro
    do lifespan(), depois de mount_module_routers()."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>SPA</html>", encoding="utf-8")

    monkeypatch.setattr(main_mod.settings, "SERVE_STATIC_FRONTEND", True)
    monkeypatch.setattr(main_mod.settings, "FRONTEND_DIST_PATH", dist)

    # _mounted_module_ids é global e persiste entre apps criados por outros
    # testes na mesma sessão pytest — sem isso, mount_module_routers() pula
    # hello_world achando que já está montado (numa app de outro teste).
    from app.module_engine.plugin_loader import _mounted_module_ids
    _mounted_module_ids.clear()

    from fastapi.testclient import TestClient
    test_app = main_mod.create_app()
    with TestClient(test_app) as client:
        resp = client.get("/api/v1/modules/hello_world/ping")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # Caminho /api/* genuinely inexistente ainda deve dar 404, não 500.
        resp_missing = client.get("/api/v1/modules/hello_world/does-not-exist")
        assert resp_missing.status_code == 404
