"""Tests for upgrade utility."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opencode_on_im.core.config import Settings
from opencode_on_im.utils.upgrade import check_upgrade


class TestUpgradeCheck:
    @pytest.mark.asyncio
    async def test_check_upgrade_success(self):
        settings = Settings()
        settings.upgrade_check_url = "https://example.com/check"
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"update_available": True, "latest_version": "1.0.0"})
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await check_upgrade(settings)
            assert result == {"update_available": True, "latest_version": "1.0.0"}
            mock_client.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_check_upgrade_failure(self):
        settings = Settings()
        
        mock_response = AsyncMock()
        mock_response.status_code = 500
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await check_upgrade(settings)
            assert result is None

    @pytest.mark.asyncio
    async def test_check_upgrade_exception(self):
        settings = Settings()
        
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Network error")
        mock_client.__aenter__.return_value = mock_client
        
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await check_upgrade(settings)
            assert result is None
