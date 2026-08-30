"""Fase 15 Slice 7 — release versioning (spec §23/§24).

PLATFORM_VERSION (app.core.settings, fonte única desde a Fase 1) validado
como SemVer via packaging.version; exposto em GET /api/v1/system/version.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_release_versioning.py -q
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

from app.core.settings import settings
from app.main import app
from app.services.versioning import is_valid_semver

pytestmark = pytest.mark.unit


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_platform_version_is_valid_semver():
    assert is_valid_semver(settings.PLATFORM_VERSION)


def test_is_valid_semver_accepts_major_minor_patch():
    assert is_valid_semver("1.4.0")


def test_is_valid_semver_accepts_prerelease():
    assert is_valid_semver("1.5.0-rc.1")


def test_is_valid_semver_rejects_malformed_string():
    assert not is_valid_semver("not-a-version")


def test_version_endpoint_returns_platform_version(client):
    response = client.get("/api/v1/system/version")
    assert response.status_code == 200
    assert response.json() == {"platform_version": settings.PLATFORM_VERSION}
