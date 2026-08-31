"""Fase 16 Slice 4 — Safe Mode (spec §16/§18).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase16_safe_mode.py -q
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

from app.main import app
from app.module_engine import plugin_loader

pytestmark = pytest.mark.integration


def test_mount_module_routers_skips_all_when_safe_mode(monkeypatch):
    monkeypatch.setenv("TECHFORGE_SAFE_MODE", "true")
    monkeypatch.setattr(plugin_loader, "_mounted_module_ids", set())

    with TestClient(app):
        pass

    assert plugin_loader._mounted_module_ids == set()


def test_platform_status_reports_safe_mode_active(monkeypatch):
    monkeypatch.setenv("TECHFORGE_SAFE_MODE", "true")
    with TestClient(app) as c:
        response = c.get("/api/v1/platform/status")
    assert response.json()["safe_mode"] is True


def test_platform_status_safe_mode_off_by_default(monkeypatch):
    monkeypatch.delenv("TECHFORGE_SAFE_MODE", raising=False)
    with TestClient(app) as c:
        response = c.get("/api/v1/platform/status")
    assert response.json()["safe_mode"] is False
