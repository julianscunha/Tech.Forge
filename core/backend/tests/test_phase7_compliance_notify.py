"""Fase 7 §15 — notificação quando módulo perde conformidade documental.

Dispara via POST /compliance/check (uso do launcher/update), não no GET
de leitura — notificação é efeito colateral de verificação, não de consulta.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase7_compliance_notify.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture()
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_compliance_check_endpoint_exists(client):
    """POST /docs/compliance/check/{module_id} retorna o relatório."""
    # hello_world pode não ter docs completos; só valida o contrato da rota
    resp = client.post("/api/v1/docs/compliance/check/hello_world")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("module_id", "is_complete", "score", "notified"):
        assert key in body


def test_compliance_check_unknown_module_404(client):
    resp = client.post("/api/v1/docs/compliance/check/nao_existe_xyz")
    assert resp.status_code == 404


def test_incomplete_module_creates_notification(client):
    """Módulo incompleto → 1 notificação warning criada (não spam)."""
    import asyncio
    from sqlalchemy import delete
    from app.db.database import AsyncSessionLocal
    from app.models.notifications import Notification

    async def _clean():
        async with AsyncSessionLocal() as s:
            await s.execute(delete(Notification).where(
                Notification.title.like("Documentation compliance%")))
            await s.commit()
    asyncio.run(_clean())

    try:
        resp = client.post("/api/v1/docs/compliance/check/hello_world")
        body = resp.json()
        if body["is_complete"]:
            assert body["notified"] is False
        else:
            assert body["notified"] is True
            # segunda chamada não duplica (dedupe por título+module)
            resp2 = client.post("/api/v1/docs/compliance/check/hello_world")
            assert resp2.status_code == 200

            async def _count():
                async with AsyncSessionLocal() as s:
                    from sqlalchemy import select, func
                    n = await s.execute(select(func.count(Notification.id)).where(
                        Notification.title.like("Documentation compliance%"),
                        Notification.module_id == "hello_world"))
                    return n.scalar()
            count = asyncio.run(_count())
            assert count == 1
    finally:
        asyncio.run(_clean())
