"""Module assets endpoint — Fase 3 §11.

Serves static frontend files of INSTALLED modules so ModuleHost can
dynamically import entry_frontend. Sandbox: resolved paths must stay
inside the module's directory.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.settings import settings

router = APIRouter()

# Extensions we are willing to serve as module frontend assets.
_ALLOWED_SUFFIXES = {
    ".js", ".mjs", ".css", ".html", ".svg", ".png", ".jpg", ".jpeg",
    ".gif", ".webp", ".woff", ".woff2", ".ttf", ".json", ".map",
}

_CONTENT_TYPES = {
    ".js": "application/javascript",
    ".mjs": "application/javascript",
    ".css": "text/css",
    ".html": "text/html",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".json": "application/json",
}


def _module_base(module_id: str) -> Path:
    """Resolve and validate the module directory. 404 if not installed."""
    base = (settings.MODULES_INSTALLED_PATH / module_id).resolve()
    installed_root = settings.MODULES_INSTALLED_PATH.resolve()
    if not base.is_dir() or installed_root not in base.parents:
        raise HTTPException(status_code=404, detail="Module not found")
    return base


@router.get("/modules/{module_id}/assets/{asset_path:path}",
            summary="Serve a static frontend asset of an installed module")
async def get_module_asset(module_id: str, asset_path: str) -> FileResponse:
    """Serve one file from the module's directory (Fase 3 §11).

    Path traversal is blocked: the resolved file must stay inside the
    module directory, and only whitelisted extensions are served.
    """
    base = _module_base(module_id)
    target = (base / asset_path).resolve()
    if base != target and base not in target.parents:
        raise HTTPException(status_code=400, detail="Invalid asset path")
    suffix = target.suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES or not target.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(
        target,
        media_type=_CONTENT_TYPES.get(suffix, "application/octet-stream"),
    )
