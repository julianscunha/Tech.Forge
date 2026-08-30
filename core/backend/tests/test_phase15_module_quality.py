"""Fase 15 Slice 10 — Module Quality / Release Readiness (spec §44/§45).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_module_quality.py -q
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

from app.main import app
from app.services.module_quality import ModuleNotFoundError, compute_module_quality

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_compute_module_quality_raises_for_unknown_module(client):
    with pytest.raises(ModuleNotFoundError):
        compute_module_quality("does_not_exist")


def test_hello_world_quality_reports_all_checks(client):
    report = compute_module_quality("hello_world")
    check_names = {c.name for c in report.checks}
    assert check_names == {"status", "documentation", "compatibility", "contract"}


def test_hello_world_is_ready(client):
    report = compute_module_quality("hello_world")
    failed = [c for c in report.checks if not c.passed]
    assert report.ready is True, f"checks falhando: {failed}"


def test_veeam_contract_check_executes_documented_examples(client):
    report = compute_module_quality("veeam_m365")
    contract_check = next(c for c in report.checks if c.name == "contract")
    assert contract_check.passed is True
    assert "exemplo" in contract_check.detail


def test_quality_endpoint_returns_report(client):
    response = client.get("/api/v1/modules/hello_world/quality")
    assert response.status_code == 200
    body = response.json()
    assert body["module_id"] == "hello_world"
    assert body["ready"] is True


def test_release_readiness_endpoint_returns_same_shape(client):
    response = client.get("/api/v1/modules/hello_world/release-readiness")
    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_quality_endpoint_404_for_unknown_module(client):
    response = client.get("/api/v1/modules/does_not_exist/quality")
    assert response.status_code == 404
