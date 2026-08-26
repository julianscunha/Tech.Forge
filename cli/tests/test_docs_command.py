"""Fase 5 Slice 1 — CLI `techforge docs` (spec §20).

Consome a API do Documentation Engine — zero duplicação de lógica.
Fallback offline: erro claro orientando subir a plataforma.

Run:  cd D:/Github/Tech.Forge && core/backend/.venv/Scripts/python.exe -m pytest cli/tests/test_docs_command.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cli"))

from techforge_cli.commands.docs import docs_cmd


@pytest.fixture()
def runner():
    return CliRunner()


def test_docs_group_exists(runner):
    result = runner.invoke(docs_cmd, ["--help"])
    assert result.exit_code == 0
    for cmd in ("list", "search", "get", "export-context"):
        assert cmd in result.output


def test_docs_list_offline_fails_cleanly(runner, monkeypatch):
    """Sem plataforma: mensagem clara, exit != 0, sem stacktrace."""
    import urllib.error

    def raise_url_error(*a, **kw):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", raise_url_error)
    result = runner.invoke(docs_cmd, ["list"])
    assert result.exit_code != 0
    assert "plataforma" in result.output.lower() or "acess" in result.output.lower()
    assert "Traceback" not in result.output


def test_docs_list_prints_titles(runner, monkeypatch):
    payload = [{"doc_id": "core/overview", "title": "Overview", "category": "core"},
               {"doc_id": "guides/dev", "title": "Dev Guide", "category": "guides"}]

    class FakeResp:
        status_code = 200
        def read(self): return __import__("json").dumps(payload).encode()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    import urllib.request
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResp())
    result = runner.invoke(docs_cmd, ["list"])
    assert result.exit_code == 0, result.output
    assert "Overview" in result.output and "Dev Guide" in result.output


def test_docs_search_passes_query(runner, monkeypatch):
    captured = {}

    class FakeResp:
        status_code = 200
        def read(self): return __import__("json").dumps(
            [{"doc_id": "x", "title": "Result", "snippet": "..."}]).encode()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def fake_urlopen(url, **kw):
        captured["url"] = url if isinstance(url, str) else url.full_url
        return FakeResp()

    import urllib.request
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = runner.invoke(docs_cmd, ["search", "lifecycle"])
    assert result.exit_code == 0, result.output
    assert "q=lifecycle" in captured["url"]
    assert "Result" in result.output


def test_docs_get_prints_article(runner, monkeypatch):
    class FakeResp:
        status_code = 200
        def read(self): return __import__("json").dumps(
            {"doc_id": "core/overview", "title": "Overview", "content": "# Conteudo aqui"}).encode()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    import urllib.request
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResp())
    result = runner.invoke(docs_cmd, ["get", "core/overview"])
    assert result.exit_code == 0, result.output
    assert "Conteudo aqui" in result.output


def test_docs_export_context_outputs_text(runner, monkeypatch):
    class FakeResp:
        status_code = 200
        def read(self): return b"# AI Context\n- modulo x"
        headers = {"Content-Type": "text/plain"}
        def __enter__(self): return self
        def __exit__(self, *a): pass

    import urllib.request
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResp())
    result = runner.invoke(docs_cmd, ["export-context"])
    assert result.exit_code == 0, result.output
    assert "AI Context" in result.output
