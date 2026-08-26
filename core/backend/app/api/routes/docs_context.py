"""Help contextual (Fase 5 §13): context_id → artigo do Documentation Engine.

Mapping declarativo em docs/context-map.yaml.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
import yaml

from app.core.settings import settings

logger = logging.getLogger("techforge.docs.context")
router = APIRouter(prefix="/docs", tags=["developer-center"])

_CONTEXT_MAP_PATH = settings.BASE_DIR / "docs" / "context-map.yaml"


def _load_map() -> dict[str, str]:
    if not _CONTEXT_MAP_PATH.is_file():
        return {}
    try:
        data = yaml.safe_load(_CONTEXT_MAP_PATH.read_text(encoding="utf-8")) or {}
        return {k: str(v) for k, v in data.items()}
    except (OSError, ValueError) as exc:
        logger.warning("Failed to load context map: %s", exc)
        return {}


@router.get("/context/{context_id}", summary="Help contextual: context_id → article")
async def get_context(context_id: str):
    """Resolve a context_id to its documentation article (spec §13)."""
    mapping = _load_map()
    doc_id = mapping.get(context_id)
    if doc_id is None:
        raise HTTPException(status_code=404,
                            detail=f"Unknown context_id '{context_id}'")

    # resolve o artigo pelo doc engine existente
    from app.doc_engine import doc_index
    entry = doc_index.get(doc_id)
    if entry is None:
        raise HTTPException(status_code=404,
                            detail=f"Mapped document '{doc_id}' not found in index")

    return {"context_id": context_id, "doc_id": doc_id, "title": entry.title}
