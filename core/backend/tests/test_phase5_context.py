"""Fase 5 Slice 2 — Help contextual: context_id → article (spec §13).

Mapping declarativo em docs/context-map.yaml.
Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase5_context.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_context_returns_article_for_known_id(client):
    resp = client.get("/api/v1/docs/context/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["context_id"] == "dashboard"
    assert data["doc_id"]          # mapeado para algum artigo


def test_context_unknown_id_404(client):
    resp = client.get("/api/v1/docs/context/nao_existe_xyz")
    assert resp.status_code == 404


def test_context_map_is_declarative_yaml():
    """O mapping vive em docs/context-map.yaml — declarativo, não hardcoded."""
    map_file = ROOT / "docs" / "context-map.yaml"
    assert map_file.is_file(), "docs/context-map.yaml deve existir"
    import yaml
    mapping = yaml.safe_load(map_file.read_text(encoding="utf-8"))
    assert "dashboard" in mapping
    # cada entrada aponta para um doc_id string
    assert all(isinstance(v, str) for v in mapping.values())


def test_context_respects_mapping_file(client):
    import yaml
    mapping = yaml.safe_load(
        (ROOT / "docs" / "context-map.yaml").read_text(encoding="utf-8"))
    first_ctx = next(iter(mapping))
    resp = client.get(f"/api/v1/docs/context/{first_ctx}")
    assert resp.status_code == 200
    assert resp.json()["doc_id"] == mapping[first_ctx]
