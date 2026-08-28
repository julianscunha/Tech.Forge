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


# ── Fase 8.1 §21 — Dependency Governance no AI Context ────────────────────────

def test_context_includes_dependency_graph_mermaid(monkeypatch, ai_context_dependencies):
    md = ai_context_dependencies
    assert "## Dependency Governance" in md
    assert "```mermaid" in md
    assert "flowchart TD" in md


def test_context_omits_dependency_section_when_no_edges(ai_context):
    """Sem dependências declaradas nos módulos reais, a seção não aparece.

    Checa o cabeçalho exato de nível 2 (não a heading nivel 3 do doc
    dependency-governance.md, que contem o mesmo texto como substring).
    """
    assert "\n## Dependency Governance\n" not in ai_context


@pytest.fixture()
def ai_context_dependencies(monkeypatch):
    from datetime import datetime
    from app.doc_engine.indexer import DocIndexer
    from app.doc_engine import doc_index, AIContextExporter
    from app.module_engine.registry import ModuleEntry, ModuleStatus

    class _FakeModuleRegistry:
        def __init__(self, entries):
            self._entries = {e.module_id: e for e in entries}

        def all(self):
            return list(self._entries.values())

        def get(self, module_id):
            return self._entries.get(module_id)

    def _entry(module_id, deps):
        return ModuleEntry(
            module_id=module_id, name=module_id, version="1.0.0",
            category="C", vendor="V", author="A", description="D",
            status=ModuleStatus.INSTALLED, install_date=datetime.now(),
            manifest_raw={"dependencies": deps},
        )

    consumer = _entry("consumer", [{"target": {"type": "module", "id": "provider"}}])
    provider = _entry("provider", [])
    fake_registry = _FakeModuleRegistry([consumer, provider])

    monkeypatch.setattr("app.module_engine.registry.registry", fake_registry)

    idx = DocIndexer(doc_index)
    idx.rebuild()
    return AIContextExporter.export(idx)
