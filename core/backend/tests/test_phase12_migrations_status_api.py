"""Fase 12 Slice 11 — GET /api/v1/system/migrations/status.

Faltava um endpoint HTTP pro frontend consultar o estado das migrations —
até aqui só existia `techforge migrations status` (CLI, acesso direto ao
Python/DB, que o navegador não tem).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_migrations_status_api.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_migrations_status_reports_head_and_current_up_to_date(client):
    resp = client.get("/api/v1/system/migrations/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["head"] == "0003"
    assert data["current"] == "0003"
    assert data["up_to_date"] is True
