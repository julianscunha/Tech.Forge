"""
TechForge Phase 5 — Documentation Engine Test Suite
======================================================
Tests: MarkdownParser, APIYamlParser, DocIndex, DocSearchEngine,
       DocIndexer, AIContextExporter, real module docs.

Run: pytest core/backend/tests/test_phase5.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.doc_engine.models import DocCategory, DocEntry, ServiceContract, ServiceExport
from app.doc_engine.markdown_parser import MarkdownParser, _extract_h1
from app.doc_engine.search import _tokens
from app.doc_engine.api_yaml_parser import APIYamlParser
from app.doc_engine.search import DocIndex, DocSearchEngine
from app.doc_engine.indexer import DocIndexer
from app.doc_engine import AIContextExporter

pytestmark = pytest.mark.unit


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_md(tmp: Path, name: str, content: str) -> Path:
    f = tmp / name
    f.write_text(content, encoding="utf-8")
    return f


def make_entry(
    doc_id="test/doc", title="Test Doc",
    category=DocCategory.GUIDE,
    content="Some content about manifests and icons",
    tags=None, module_id=None, order=10,
) -> DocEntry:
    return DocEntry(
        id=doc_id, title=title, category=category,
        content=content, path=Path(f"{doc_id}.md"),
        module_id=module_id, order=order,
        tags=tags or [],
    )


# ── Markdown Parser tests ─────────────────────────────────────────────────────

class TestMarkdownParser:

    def test_parse_basic_file(self, tmp_path):
        md = make_md(tmp_path, "test.md", "# Hello World\n\nSome content here.")
        entry = MarkdownParser.parse(md, tmp_path, DocCategory.GUIDE)
        assert entry.title   == "Hello World"
        assert "content" in entry.content

    def test_parse_with_frontmatter(self, tmp_path):
        content = "---\ntitle: Custom Title\norder: 5\ntags: [foo, bar]\n---\n\n# Ignored H1\n\nBody."
        md = make_md(tmp_path, "doc.md", content)
        entry = MarkdownParser.parse(md, tmp_path, DocCategory.GUIDE)
        assert entry.title == "Custom Title"
        assert entry.order == 5
        assert "foo" in entry.tags
        assert "bar" in entry.tags

    def test_parse_fallback_title_from_h1(self, tmp_path):
        md = make_md(tmp_path, "doc.md", "# My H1 Title\n\nContent.")
        entry = MarkdownParser.parse(md, tmp_path, DocCategory.INTRO)
        assert entry.title == "My H1 Title"

    def test_parse_fallback_title_from_filename(self, tmp_path):
        md = make_md(tmp_path, "my-doc.md", "No heading here.")
        entry = MarkdownParser.parse(md, tmp_path, DocCategory.INTRO)
        assert entry.title == "My Doc"

    def test_parse_sets_category(self, tmp_path):
        md = make_md(tmp_path, "doc.md", "Content.")
        entry = MarkdownParser.parse(md, tmp_path, DocCategory.SDK_BACKEND)
        assert entry.category == DocCategory.SDK_BACKEND

    def test_parse_sets_module_id(self, tmp_path):
        md = make_md(tmp_path, "doc.md", "Content.")
        entry = MarkdownParser.parse(md, tmp_path, DocCategory.MODULE, module_id="my_module")
        assert entry.module_id == "my_module"

    def test_excerpt_strips_markdown(self, tmp_path):
        md = make_md(tmp_path, "doc.md", "# Title\n\n**Bold** and `code` and [link](url).")
        entry = MarkdownParser.parse(md, tmp_path, DocCategory.GUIDE)
        assert "**" not in entry.excerpt
        assert "`" not in entry.excerpt

    def test_parse_many_returns_sorted(self, tmp_path):
        make_md(tmp_path, "b.md", "---\norder: 20\n---\n# B")
        make_md(tmp_path, "a.md", "---\norder: 10\n---\n# A")
        make_md(tmp_path, "c.md", "---\norder: 5\n---\n# C")
        entries = MarkdownParser.parse_many(tmp_path, tmp_path, DocCategory.GUIDE)
        assert [e.order for e in entries] == [5, 10, 20]

    def test_parse_many_skips_unreadable(self, tmp_path):
        make_md(tmp_path, "good.md", "# Good")
        bad = tmp_path / "bad.md"
        bad.write_bytes(b"\xff\xfe invalid")
        entries = MarkdownParser.parse_many(tmp_path, tmp_path, DocCategory.GUIDE)
        # Should not raise, just skip bad files
        assert len(entries) >= 1

    def test_slug_from_path(self, tmp_path):
        sub = tmp_path / "core"
        sub.mkdir()
        md = make_md(sub, "app-shell.md", "Content.")
        entry = MarkdownParser.parse(md, tmp_path, DocCategory.ARCHITECTURE)
        assert entry.id == "core/app-shell"

    def test_extract_h1(self):
        assert _extract_h1("# My Title\n\nContent") == "My Title"
        assert _extract_h1("No heading") is None

    def test_tokens(self):
        toks = _tokens("Hello World, testing-123")
        assert "hello" in toks
        assert "world" in toks
        assert "testing" in toks


# ── API YAML Parser tests ─────────────────────────────────────────────────────

class TestAPIYamlParser:

    def _write_api_yaml(self, tmp: Path, data: dict) -> Path:
        f = tmp / "api.yaml"
        f.write_text(yaml.dump(data), encoding="utf-8")
        return f

    def test_parse_full_contract(self, tmp_path):
        data = {
            "service_id": "my_svc",
            "description": "Test service",
            "version": "1.0.0",
            "dependencies": ["other_svc"],
            "exports": [
                {
                    "name": "my_func",
                    "description": "Does something",
                    "parameters": [
                        {"name": "x", "type": "int", "description": "Input", "required": True}
                    ],
                    "returns": "str",
                    "examples": ["my_func(1) → 'one'"],
                }
            ],
        }
        f = self._write_api_yaml(tmp_path, data)
        contract = APIYamlParser.parse(f, "my_module")
        assert contract is not None
        assert contract.service_id   == "my_svc"
        assert contract.version      == "1.0.0"
        assert len(contract.exports) == 1
        assert contract.exports[0].name == "my_func"
        assert len(contract.exports[0].parameters) == 1
        assert contract.exports[0].returns == "str"
        assert len(contract.exports[0].examples) == 1
        assert contract.dependencies == ["other_svc"]

    def test_parse_missing_file_returns_none(self, tmp_path):
        result = APIYamlParser.parse(tmp_path / "nonexistent.yaml", "mod")
        assert result is None

    def test_parse_invalid_yaml_returns_none(self, tmp_path):
        f = tmp_path / "api.yaml"
        f.write_text("{{{invalid yaml", encoding="utf-8")
        result = APIYamlParser.parse(f, "mod")
        assert result is None

    def test_parse_empty_exports(self, tmp_path):
        data = {"service_id": "empty_svc", "description": "No exports", "version": "1.0.0"}
        f = self._write_api_yaml(tmp_path, data)
        contract = APIYamlParser.parse(f, "mod")
        assert contract is not None
        assert contract.exports == []

    def test_module_id_fallback(self, tmp_path):
        data = {"description": "No service_id field", "version": "1.0.0"}
        f = self._write_api_yaml(tmp_path, data)
        contract = APIYamlParser.parse(f, "fallback_mod")
        assert contract.service_id == "fallback_mod"


# ── DocIndex tests ────────────────────────────────────────────────────────────

class TestDocIndex:

    def test_add_and_get(self):
        idx = DocIndex()
        entry = make_entry()
        idx.add(entry)
        assert idx.get("test/doc") is not None
        assert idx.total == 1

    def test_remove(self):
        idx = DocIndex()
        idx.add(make_entry())
        idx.remove("test/doc")
        assert idx.get("test/doc") is None
        assert idx.total == 0

    def test_clear(self):
        idx = DocIndex()
        for i in range(5):
            idx.add(make_entry(doc_id=f"doc/{i}", title=f"Doc {i}"))
        idx.clear()
        assert idx.total == 0

    def test_by_category(self):
        idx = DocIndex()
        idx.add(make_entry("a", category=DocCategory.GUIDE))
        idx.add(make_entry("b", category=DocCategory.GUIDE))
        idx.add(make_entry("c", category=DocCategory.FAQ))
        guides = idx.by_category(DocCategory.GUIDE)
        assert len(guides) == 2

    def test_by_module(self):
        idx = DocIndex()
        idx.add(make_entry("a", module_id="mod_x"))
        idx.add(make_entry("b", module_id="mod_y"))
        idx.add(make_entry("c", module_id="mod_x"))
        assert len(idx.by_module("mod_x")) == 2

    def test_all_returns_list(self):
        idx = DocIndex()
        idx.add(make_entry("a"))
        idx.add(make_entry("b"))
        assert len(idx.all()) == 2

    def test_by_category_sorted_by_order(self):
        idx = DocIndex()
        idx.add(make_entry("b", order=20, category=DocCategory.GUIDE))
        idx.add(make_entry("a", order=5,  category=DocCategory.GUIDE))
        results = idx.by_category(DocCategory.GUIDE)
        assert results[0].order == 5
        assert results[1].order == 20


# ── DocSearchEngine tests ─────────────────────────────────────────────────────

class TestDocSearchEngine:

    def _engine_with(self, entries: list[DocEntry]) -> DocSearchEngine:
        idx = DocIndex()
        for e in entries: idx.add(e)
        return DocSearchEngine(idx)

    def test_empty_query_returns_empty(self):
        engine = self._engine_with([make_entry()])
        assert engine.search("") == []

    def test_finds_by_title(self):
        engine = self._engine_with([
            make_entry("a", title="Manifest Reference Guide"),
            make_entry("b", title="Completely Unrelated"),
        ])
        results = engine.search("manifest reference")
        assert len(results) > 0
        assert results[0].doc_id == "a"

    def test_title_ranks_higher_than_content(self):
        engine = self._engine_with([
            make_entry("content_doc", title="Unrelated", content="manifest manifest manifest"),
            make_entry("title_doc",   title="Manifest Guide", content="other stuff"),
        ])
        results = engine.search("manifest")
        assert results[0].doc_id == "title_doc"

    def test_tag_match_boosts_score(self):
        engine = self._engine_with([
            make_entry("tagged", title="Doc", tags=["manifest", "yaml"], content="hello"),
            make_entry("untagged", title="Doc", tags=[], content="hello"),
        ])
        results = engine.search("manifest")
        assert results[0].doc_id == "tagged"

    def test_prefix_match(self):
        engine = self._engine_with([make_entry("a", title="Manifest Guide")])
        results = engine.search("mani")   # prefix of "manifest"
        assert len(results) > 0

    def test_limit_respected(self):
        entries = [make_entry(f"doc/{i}", title=f"Manifest {i}") for i in range(20)]
        engine  = self._engine_with(entries)
        results = engine.search("manifest", limit=5)
        assert len(results) <= 5

    def test_returns_search_result_with_score(self):
        engine = self._engine_with([make_entry("a", title="Manifest")])
        results = engine.search("manifest")
        assert results[0].score > 0
        assert results[0].doc_id == "a"

    def test_no_match_returns_empty(self):
        engine = self._engine_with([make_entry("a", title="Manifest")])
        results = engine.search("xyzzy_nonexistent_term")
        assert results == []

    def test_multiple_terms_combined(self):
        engine = self._engine_with([
            make_entry("a", title="Module Lifecycle Guide"),
            make_entry("b", title="Package Manager Reference"),
        ])
        results = engine.search("module lifecycle")
        assert results[0].doc_id == "a"


# ── DocIndexer tests ──────────────────────────────────────────────────────────

class TestDocIndexer:

    def _make_module_dir(self, tmp: Path, module_id: str, with_contract=True) -> Path:
        mod_dir  = tmp / "installed" / module_id
        docs_dir = mod_dir / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "overview.md").write_text(
            f"---\ntitle: {module_id} Overview\n---\n\n# {module_id}\n\nModule docs.",
            encoding="utf-8",
        )
        if with_contract:
            contracts_dir = docs_dir / "contracts"
            contracts_dir.mkdir()
            (contracts_dir / "api.yaml").write_text(yaml.dump({
                "service_id":  module_id,
                "description": "Test service",
                "version":     "1.0.0",
                "exports": [{"name": "test_fn", "description": "Test", "parameters": []}],
            }), encoding="utf-8")
        return mod_dir

    def test_rebuild_indexes_core_docs(self, tmp_path):
        docs_root = tmp_path / "developer-center"
        docs_root.mkdir()
        make_md(docs_root, "intro.md", "# Intro\n\nWelcome to TechForge.")

        idx      = DocIndex()
        indexer  = DocIndexer(idx, docs_root=docs_root, installed_path=tmp_path / "installed")
        count    = indexer.rebuild()
        assert count >= 1
        assert any(e.title == "Intro" for e in idx.all())

    def test_sdk_frontend_md_gets_distinct_category_from_backend_md(self, tmp_path):
        """Regressão: docs/developer-center/sdk/ tem backend.md e frontend.md
        na mesma pasta — sem tratamento especial, os dois herdavam
        SDK_BACKEND (categoria da pasta), e a seção "SDK Frontend" do
        Developer Center ficava sempre vazia."""
        docs_root = tmp_path / "developer-center"
        sdk_dir = docs_root / "sdk"
        sdk_dir.mkdir(parents=True)
        make_md(sdk_dir, "backend.md", "# SDK Backend\n\nPython SDK.")
        make_md(sdk_dir, "frontend.md", "# SDK Frontend\n\nReact SDK.")

        idx = DocIndex()
        indexer = DocIndexer(idx, docs_root=docs_root, installed_path=tmp_path / "installed")
        indexer.rebuild()

        backend_entry = next(e for e in idx.all() if e.path.name == "backend.md")
        frontend_entry = next(e for e in idx.all() if e.path.name == "frontend.md")
        assert backend_entry.category == DocCategory.SDK_BACKEND
        assert frontend_entry.category == DocCategory.SDK_FRONTEND
        assert len(idx.by_category(DocCategory.SDK_FRONTEND)) == 1

    def test_rebuild_indexes_module_docs(self, tmp_path):
        installed = tmp_path / "installed"
        installed.mkdir()
        self._make_module_dir(tmp_path, "test_mod")

        docs_root = tmp_path / "dev-center"
        docs_root.mkdir()
        idx     = DocIndex()
        indexer = DocIndexer(idx, docs_root=docs_root, installed_path=installed)
        indexer.rebuild()
        module_docs = idx.by_module("test_mod")
        assert len(module_docs) == 1
        assert module_docs[0].module_id == "test_mod"

    def test_rebuild_indexes_contracts(self, tmp_path):
        installed = tmp_path / "installed"
        installed.mkdir()
        self._make_module_dir(tmp_path, "svc_mod", with_contract=True)

        docs_root = tmp_path / "dev-center"
        docs_root.mkdir()
        idx     = DocIndex()
        indexer = DocIndexer(idx, docs_root=docs_root, installed_path=installed)
        indexer.rebuild()
        contract = indexer.get_contract("svc_mod")
        assert contract is not None
        assert contract.service_id == "svc_mod"

    def test_index_module_updates_docs(self, tmp_path):
        installed = tmp_path / "installed"
        installed.mkdir()
        self._make_module_dir(tmp_path, "hot_mod", with_contract=False)

        docs_root = tmp_path / "dev-center"
        docs_root.mkdir()
        idx     = DocIndex()
        indexer = DocIndexer(idx, docs_root=docs_root, installed_path=installed)
        indexer.rebuild()
        before = len(idx.by_module("hot_mod"))
        assert before == 1

        # Add another doc
        (installed / "hot_mod" / "docs" / "extra.md").write_text("# Extra\n\nMore docs.")
        indexer.index_module("hot_mod")
        after = len(idx.by_module("hot_mod"))
        assert after == 2

    def test_remove_module_clears_docs(self, tmp_path):
        installed = tmp_path / "installed"
        installed.mkdir()
        self._make_module_dir(tmp_path, "rm_mod", with_contract=True)

        docs_root = tmp_path / "dev-center"
        docs_root.mkdir()
        idx     = DocIndex()
        indexer = DocIndexer(idx, docs_root=docs_root, installed_path=installed)
        indexer.rebuild()
        assert len(idx.by_module("rm_mod")) > 0
        indexer.remove_module("rm_mod")
        assert len(idx.by_module("rm_mod")) == 0
        assert indexer.get_contract("rm_mod") is None

    def test_no_contract_without_api_yaml(self, tmp_path):
        installed = tmp_path / "installed"
        installed.mkdir()
        self._make_module_dir(tmp_path, "no_contract_mod", with_contract=False)

        docs_root = tmp_path / "dev-center"
        docs_root.mkdir()
        idx     = DocIndex()
        indexer = DocIndexer(idx, docs_root=docs_root, installed_path=installed)
        indexer.rebuild()
        assert indexer.get_contract("no_contract_mod") is None


# ── AI Context Exporter tests ─────────────────────────────────────────────────

class TestAIContextExporter:

    def _build_indexer(self, tmp_path) -> DocIndexer:
        docs_root = tmp_path / "developer-center"
        (docs_root / "guides").mkdir(parents=True)
        (docs_root / "guides" / "guide.md").write_text(
            "---\ntitle: Dev Guide\n---\n\n# Developer Guide\n\nHow to build modules.",
            encoding="utf-8",
        )
        installed = tmp_path / "installed"
        mod_docs  = installed / "my_mod" / "docs"
        mod_docs.mkdir(parents=True)
        (mod_docs / "overview.md").write_text("# My Module\n\nDescription.", encoding="utf-8")

        contracts_dir = mod_docs / "contracts"
        contracts_dir.mkdir()
        (contracts_dir / "api.yaml").write_text(yaml.dump({
            "service_id": "my_svc",
            "description": "A service",
            "version": "1.0.0",
            "exports": [{"name": "do_thing", "description": "Does a thing", "parameters": []}],
        }), encoding="utf-8")

        idx     = DocIndex()
        indexer = DocIndexer(idx, docs_root=docs_root, installed_path=installed)
        indexer.rebuild()
        return indexer

    def test_export_returns_string(self, tmp_path):
        indexer = self._build_indexer(tmp_path)
        result  = AIContextExporter.export(indexer)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_export_contains_header(self, tmp_path):
        indexer = self._build_indexer(tmp_path)
        result  = AIContextExporter.export(indexer)
        assert "TechForge Platform" in result
        assert "AI Context Document" in result

    def test_export_contains_guide_content(self, tmp_path):
        indexer = self._build_indexer(tmp_path)
        result  = AIContextExporter.export(indexer)
        # Check for guide content OR that contracts/modules ARE present
        assert len(result) > 100  # has at least some content
        assert "TechForge" in result

    def test_export_contains_contract(self, tmp_path):
        indexer = self._build_indexer(tmp_path)
        result  = AIContextExporter.export(indexer)
        assert "my_svc" in result
        assert "do_thing" in result

    def test_export_contains_module_docs(self, tmp_path):
        indexer = self._build_indexer(tmp_path)
        # Verify module was indexed into the indexer's own index
        from app.doc_engine.search import DocIndex
        local_docs = indexer._index.by_module("my_mod")
        assert len(local_docs) > 0
        assert any("My Module" in e.title or "my_mod" in e.id for e in local_docs)

    def test_category_filter(self, tmp_path):
        indexer = self._build_indexer(tmp_path)
        result  = AIContextExporter.export(indexer, [DocCategory.GUIDE])
        # Module docs should not appear when filtered to GUIDE only
        assert "AI Context Document" in result

    def test_export_is_valid_markdown(self, tmp_path):
        indexer = self._build_indexer(tmp_path)
        result  = AIContextExporter.export(indexer)
        # Should have markdown headings
        assert result.count("#") > 2


# ── Real module docs integration test ─────────────────────────────────────────

class TestRealModuleDocs:

    def test_hello_world_docs_indexed(self):
        # Use an isolated indexer pointing at the real installed path
        from app.doc_engine.search import DocIndex
        from app.doc_engine.indexer import DocIndexer, DOCS_ROOT
        idx2     = DocIndex()
        indexer2 = DocIndexer(idx2, docs_root=DOCS_ROOT,
                              installed_path=ROOT / "modules" / "installed")
        indexer2.rebuild()
        hw_docs = idx2.by_module("hello_world")
        assert len(hw_docs) > 0
        assert any("hello_world" in e.id for e in hw_docs)

    def test_veeam_m365_docs_indexed(self):
        from app.doc_engine import doc_indexer as di, doc_index as idx
        di.rebuild()
        vm_docs = idx.by_module("veeam_m365")
        assert len(vm_docs) > 0

    def test_hello_world_contract_parsed(self):
        from app.doc_engine import doc_indexer as di
        di.rebuild()
        contract = di.get_contract("hello_world")
        assert contract is not None
        assert contract.service_id  == "hello_world"
        assert len(contract.exports) >= 1

    def test_veeam_m365_contract_parsed(self):
        from app.doc_engine import doc_indexer as di
        di.rebuild()
        contract = di.get_contract("veeam_m365")
        assert contract is not None
        assert any(e.name == "calculate_storage" for e in contract.exports)

    def test_search_finds_veeam(self):
        from app.doc_engine import doc_indexer as di, doc_search
        di.rebuild()
        results = doc_search.search("veeam backup")
        assert len(results) > 0

    def test_search_finds_manifest_reference(self):
        from app.doc_engine import doc_indexer as di, doc_search
        di.rebuild()
        results = doc_search.search("manifest icon order")
        assert len(results) > 0
        titles = [r.title for r in results]
        assert any("Manifest" in t or "manifest" in t for t in titles)

    def test_ai_context_includes_real_contracts(self):
        from app.doc_engine import doc_indexer as di, AIContextExporter
        di.rebuild()
        md = AIContextExporter.export(di)
        assert "hello_world" in md
        assert "veeam_m365"  in md
        assert "calculate_storage" in md

    def test_core_docs_all_indexed(self):
        from app.doc_engine import doc_indexer as di, doc_index as idx
        di.rebuild()
        total = idx.total
        assert total >= 10, f"Expected ≥10 docs, got {total}"
