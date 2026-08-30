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
