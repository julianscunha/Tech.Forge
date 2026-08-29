"""/api/v1/config — Fase 12 §9/§16/§29.

Configuração de plataforma efetiva. Sem prefixo próprio — path literal do
spec é `GET /api/v1/config`, não `/system/config` nem `/platform/config`.
Serve também de "export" (§16): `settings.py` nunca guarda segredo (§9
exige isso), então o mesmo payload de leitura já é seguro de exportar.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.settings import settings

router = APIRouter(tags=["config"])


@router.get("/config", summary="Platform configuration (Fase 12)")
async def get_platform_config() -> dict:
    return settings.model_dump(mode="json")
