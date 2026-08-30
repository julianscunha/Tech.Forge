"""Fase 8 §24 — CLI `techforge services`.

Consome a API do Service Registry (/api/v1/services*) — zero duplicação de
lógica, mesmo padrão de cli/techforge_cli/commands/docs.py.

Run:  cd D:/Github/Tech.Forge && core/backend/.venv/Scripts/python.exe -m pytest cli/tests/test_services_command.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cli"))

from techforge_cli.commands.services import services_cmd

pytestmark = pytest.mark.integration


@pytest.fixture()
def runner():
    return CliRunner()


class FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_services_group_exists(runner):
    result = runner.invoke(services_cmd, ["--help"])
    assert result.exit_code == 0
    for cmd in ("list", "show", "capabilities", "contract", "status"):
        assert cmd in result.output


def test_services_list_offline_fails_cleanly(runner, monkeypatch):
    import urllib.error

    def raise_url_error(*a, **kw):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", raise_url_error)
    result = runner.invoke(services_cmd, ["list"])
    assert result.exit_code != 0
    assert "plataforma" in result.output.lower() or "acess" in result.output.lower()
    assert "Traceback" not in result.output


def test_services_list_prints_service_ids(runner, monkeypatch):
    payload = [{"service_id": "hello_world", "module_id": "hello_world",
                "status": "ACTIVE", "capabilities": ["hello_world.ping"]}]
    import urllib.request
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResp(payload))
    result = runner.invoke(services_cmd, ["list"])
    assert result.exit_code == 0, result.output
    assert "hello_world" in result.output
    assert "ACTIVE" in result.output


def test_services_show_prints_descriptor(runner, monkeypatch):
    payload = {"service_id": "hello_world", "module_id": "hello_world",
               "status": "ACTIVE", "capabilities": ["hello_world.ping"],
               "module_version": "1.0.0", "service_version": "1.0.0", "contract": None}
    import urllib.request
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResp(payload))
    result = runner.invoke(services_cmd, ["show", "hello_world"])
    assert result.exit_code == 0, result.output
    assert "hello_world" in result.output


def test_services_capabilities_prints_map(runner, monkeypatch):
    payload = {"hello_world.ping": ["hello_world"]}
    import urllib.request
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResp(payload))
    result = runner.invoke(services_cmd, ["capabilities"])
    assert result.exit_code == 0, result.output
    assert "hello_world.ping" in result.output


def test_services_contract_prints_exports(runner, monkeypatch):
    payload = {"service_id": "hello_world", "module_id": "hello_world",
               "description": "d", "version": "1.0.0", "dependencies": [],
               "capabilities": [], "exports": [{"name": "ping", "description": "d",
               "parameters": [], "returns": None, "examples": []}]}
    import urllib.request
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResp(payload))
    result = runner.invoke(services_cmd, ["contract", "hello_world"])
    assert result.exit_code == 0, result.output
    assert "ping" in result.output


def test_services_search_prints_matches(runner, monkeypatch):
    payload = [{"service_id": "aws.costs", "module_id": "aws_cost_service",
                "status": "ACTIVE", "capabilities": ["aws.cost.read"]}]
    captured = {}

    def fake_urlopen(url, **kw):
        captured["url"] = url if isinstance(url, str) else url.full_url
        return FakeResp(payload)

    import urllib.request
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = runner.invoke(services_cmd, ["search", "cost"])
    assert result.exit_code == 0, result.output
    assert "q=cost" in captured["url"]
    assert "aws.costs" in result.output


def test_services_search_no_match_prints_message(runner, monkeypatch):
    import urllib.request
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResp([]))
    result = runner.invoke(services_cmd, ["search", "nonexistent"])
    assert result.exit_code == 0, result.output
    assert "nonexistent" in result.output.lower() or "nenhum" in result.output.lower()


def test_services_status_prints_summary(runner, monkeypatch):
    payload = [
        {"service_id": "a", "module_id": "a", "status": "ACTIVE", "capabilities": []},
        {"service_id": "b", "module_id": "b", "status": "FAILED", "capabilities": []},
    ]
    import urllib.request
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: FakeResp(payload))
    result = runner.invoke(services_cmd, ["status"])
    assert result.exit_code == 0, result.output
    assert "ACTIVE" in result.output and "FAILED" in result.output
