"""Fase 4 Slice 2 — Modelo de origem + integração NotificationsSDK→Core.

Spec Fase 4 §4: origem catalog | local | development preservada.
Spec §20 + diretriz do usuário: sdk.notifications.push() entrega no Core.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase4_source.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core" / "backend"))
sys.path.insert(0, str(ROOT / "sdk" / "python"))


# ── Source model ─────────────────────────────────────────────────────────────

def test_module_model_has_source_fields():
    from app.models.registry import Module
    import inspect
    cols = inspect.getsource(Module)
    assert "source_type" in cols
    assert "source_location" in cols


def test_install_sets_local_source():
    """Instalação por .mod local → source_type='local'."""
    from app.package_manager.manager import PackageManager

    src = inspect_getsource(PackageManager.install)
    assert "source" in src


def inspect_getsource(fn):
    import inspect
    return inspect.getsource(fn)


# ── SDK notifications → Core ────────────────────────────────────────────────

def test_sdk_notifications_push_delivers_to_core_api(tmp_path, monkeypatch):
    """push() deve chamar POST /api/v1/notifications com module_id."""
    from techforge_sdk.notifications import NotificationsSDK

    calls = []

    class FakeResponse:
        status_code = 201
        def json(self):
            return {}

    def fake_urlopen(req, timeout=None):
        import urllib.request
        calls.append((req.full_url, req.data.decode("utf-8")))
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    sdk = NotificationsSDK("demo_mod")
    sdk.core_api_url = "http://127.0.0.1:8000/api/v1"
    sdk.http_enabled = True
    result = sdk.push(title="Backup done", message="3 VMs", level="success")

    assert len(calls) == 1
    url, body = calls[0]
    assert url.endswith("/notifications")
    assert '"module_id"' in body and "demo_mod" in body


def test_sdk_push_falls_back_to_queue_when_http_disabled(tmp_path):
    """Sem plataforma no ar, push mantém a notificação na fila local."""
    from techforge_sdk.notifications import NotificationsSDK

    sdk = NotificationsSDK("offline_mod")
    sdk.http_enabled = False
    before = len(sdk._queue)
    sdk.push(title="t", message="m", level="info")
    assert len(sdk._queue) == before + 1
