"""Fase 7 §17 — contexto para IA inclui governança documental (DoD).

Uma IA que receba o contexto oficial deve saber os requisitos documentais.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase7_ai_context.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))


@pytest.fixture()
def ai_context():
    from app.doc_engine.indexer import DocIndexer
    from app.doc_engine import doc_index
    from app.doc_engine import AIContextExporter

    idx = DocIndexer(doc_index)
    idx.rebuild()
    return AIContextExporter.export(idx)


def test_context_includes_documentation_first(ai_context):
    """Governança Documentation First presente no export."""
    assert "documentation-first-principle" in ai_context


def test_context_includes_dod_requirements(ai_context):
    """Definition of Done documental explicado no export."""
    low = ai_context.lower()
    assert "definition of done" in low or "dod" in low


def test_governance_doc_indexed():
    """O doc de governança está no índice (fonte do export)."""
    from app.doc_engine.indexer import DocIndexer
    from app.doc_engine import doc_index

    DocIndexer(doc_index).rebuild()
    entry = doc_index.get("governance/documentation-first-principle")
    assert entry is not None
