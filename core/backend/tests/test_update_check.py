"""
Update Check — compara PLATFORM_VERSION local com a release mais recente
publicada no GitHub (app.services.update_check).
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

pytestmark = pytest.mark.unit


def _mock_client(response: MagicMock | None = None, raises: Exception | None = None):
    mock_client = MagicMock()
    if raises is not None:
        async def mock_get(*args, **kwargs):
            raise raises
        mock_client.get = mock_get
    else:
        async def mock_get(*args, **kwargs):
            return response
        mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestCheckForUpdate:

    @pytest.mark.asyncio
    async def test_reports_update_available_when_remote_tag_is_newer(self):
        from app.core.settings import settings
        from app.services.update_check import check_for_update

        response = MagicMock()
        response.json.return_value = {
            "tag_name": "v99.0.0",
            "html_url": "https://example.com/releases/v99.0.0",
            "body": "- Fixed things\n- Added stuff",
        }
        response.raise_for_status = MagicMock()

        with patch.object(settings, "PLATFORM_VERSION", "1.0.0"), \
             patch("httpx.AsyncClient", return_value=_mock_client(response)):
            result = await check_for_update()

        assert result.update_available is True
        assert result.latest_version == "99.0.0"
        assert result.release_url == "https://example.com/releases/v99.0.0"
        assert result.release_notes == "- Fixed things\n- Added stuff"

    @pytest.mark.asyncio
    async def test_no_update_when_local_is_current(self):
        from app.core.settings import settings
        from app.services.update_check import check_for_update

        response = MagicMock()
        response.json.return_value = {"tag_name": "v1.0.0", "html_url": "https://example.com"}
        response.raise_for_status = MagicMock()

        with patch.object(settings, "PLATFORM_VERSION", "1.0.0"), \
             patch("httpx.AsyncClient", return_value=_mock_client(response)):
            result = await check_for_update()

        assert result.update_available is False
        assert result.current_version == "1.0.0"

    @pytest.mark.asyncio
    async def test_network_error_returns_no_update_without_raising(self):
        import httpx
        from app.services.update_check import check_for_update

        with patch("httpx.AsyncClient", return_value=_mock_client(raises=httpx.ConnectError("offline"))):
            result = await check_for_update()

        assert result.update_available is False
        assert result.latest_version is None
