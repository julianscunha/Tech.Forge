"""Notification Foundation.

Estrutura simples de notificações do Core com níveis info/warning/error/success.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase2_notifications.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    with TestClient(app) as c:
        # isolate each test with a clean slate
        from app.db.database import AsyncSessionLocal
        import asyncio
        from sqlalchemy import delete
        from app.models.notifications import Notification

        async def _clean():
            async with AsyncSessionLocal() as s:
                await s.execute(delete(Notification))
                await s.commit()
        asyncio.run(_clean())
        yield c
        asyncio.run(_clean())


def test_create_notification_each_level(client):
    for level in ("info", "warning", "error", "success"):
        resp = client.post(
            "/api/v1/notifications",
            json={"level": level, "title": f"t-{level}", "message": "m"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["level"] == level
        assert data["read"] is False


def test_create_rejects_invalid_level(client):
    resp = client.post(
        "/api/v1/notifications",
        json={"level": "critical", "title": "t", "message": "m"},
    )
    assert resp.status_code == 422


def test_list_and_unread_count(client):
    for i in range(3):
        client.post("/api/v1/notifications",
                    json={"level": "info", "title": f"n{i}", "message": "m"})
    data = client.get("/api/v1/notifications").json()
    assert len(data) == 3
    assert client.get("/api/v1/notifications/unread-count").json()["count"] == 3


def test_mark_read_and_read_all(client):
    nid = client.post("/api/v1/notifications",
                      json={"level": "warning", "title": "w", "message": "m"}).json()["id"]
    assert client.post(f"/api/v1/notifications/{nid}/read").status_code == 200
    assert client.get("/api/v1/notifications/unread-count").json()["count"] == 0

    client.post("/api/v1/notifications", json={"level": "error", "title": "e", "message": "m"})
    assert client.get("/api/v1/notifications/unread-count").json()["count"] == 1
    assert client.post("/api/v1/notifications/read-all").status_code == 200
    assert client.get("/api/v1/notifications/unread-count").json()["count"] == 0


def test_unread_only_filter(client):
    a = client.post("/api/v1/notifications",
                    json={"level": "info", "title": "a", "message": "m"}).json()
    client.post("/api/v1/notifications", json={"level": "info", "title": "b", "message": "m"})
    client.post(f"/api/v1/notifications/{a['id']}/read")
    unread = client.get("/api/v1/notifications", params={"unread_only": True}).json()
    assert [n["title"] for n in unread] == ["b"]


def test_notification_title_min_length(client):
    """Quality pass Fase 2: title vazio deve ser rejeitado (422)."""
    resp = client.post("/api/v1/notifications",
                       json={"level": "info", "title": "", "message": "m"})
    assert resp.status_code == 422
