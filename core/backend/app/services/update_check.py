"""
Update Check — compara PLATFORM_VERSION local com a última release
publicada em github.com/{settings.PLATFORM_REPO_SLUG}.

Falha de rede (desktop offline) não é erro — só significa "sem info de
update agora"; nunca deve quebrar o Dashboard/Sidebar.
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx
from packaging.version import InvalidVersion, Version
from pydantic import BaseModel

from app.core.settings import settings

logger = logging.getLogger("techforge.update_check")


class UpdateCheckResult(BaseModel):
    current_version: str
    latest_version: Optional[str] = None
    update_available: bool = False
    release_url: Optional[str] = None
    release_notes: Optional[str] = None


async def check_for_update() -> UpdateCheckResult:
    current = settings.PLATFORM_VERSION
    url = f"https://api.github.com/repos/{settings.PLATFORM_REPO_SLUG}/releases/latest"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers={"Accept": "application/vnd.github+json"})
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.debug("Update check indisponível (offline ou rate-limited?): %s", exc)
        return UpdateCheckResult(current_version=current)

    latest = str(data.get("tag_name", "")).lstrip("v")
    try:
        update_available = bool(latest) and Version(latest) > Version(current)
    except InvalidVersion:
        update_available = False

    return UpdateCheckResult(
        current_version=current,
        latest_version=latest or None,
        update_available=update_available,
        release_url=data.get("html_url"),
        release_notes=data.get("body") or None,
    )
