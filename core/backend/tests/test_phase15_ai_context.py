"""Fase 15 Slice 14 — AI Context inclui Definition of Done (spec §29/§43).

`category: core-architecture` no frontmatter é suficiente pro DocIndexer
indexar automaticamente (mesmo mecanismo confirmado na Fase 12 pra
persistence.md) — nenhum arquivo de AI Context manual necessário.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_ai_context.py -q
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

from app.main import app

pytestmark = pytest.mark.integration


def test_ai_context_export_includes_quality_and_release_doc():
    with TestClient(app) as client:
        response = client.get("/api/v1/docs/export/ai-context")
    assert response.status_code == 200
    text = response.text
    assert "Definition of Done" in text
    assert "Release Readiness Report" in text
