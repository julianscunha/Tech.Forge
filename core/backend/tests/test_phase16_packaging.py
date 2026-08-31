"""Fase 16 Slice 7 — entry point do backend empacotado (spec §10).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase16_packaging.py -q
"""
from __future__ import annotations

import pytest

import techforge_server

pytestmark = pytest.mark.unit


def test_main_runs_uvicorn_with_configured_host_and_port(monkeypatch):
    # Passa o objeto `app` direto (não a string "app.main:app") — import-by-
    # string do uvicorn falha dentro do executável congelado pelo PyInstaller.
    captured: dict = {}
    monkeypatch.setattr(
        techforge_server.uvicorn, "run",
        lambda app, host, port, reload: captured.update(app=app, host=host, port=port, reload=reload),
    )

    techforge_server.main()

    assert captured["app"] is techforge_server.app
    assert captured["reload"] is False
    assert captured["host"] and captured["port"]
