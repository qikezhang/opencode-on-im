"""Tests for main Application class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opencode_on_im.core.app import Application
from opencode_on_im.core.config import Settings


class TestApplication:
    @pytest.fixture
    def settings(self):
        settings = Settings()
        settings.telegram.token = None  # Disable by default
        settings.dingtalk.app_key = None
        settings.upgrade_check_enabled = False
        return settings

    @pytest.fixture
    def app(self, settings):
        with patch("opencode_on_im.core.app.SessionManager"), \
             patch("opencode_on_im.core.app.InstanceRegistry"), \
             patch("opencode_on_im.core.app.NotificationRouter"), \
             patch("opencode_on_im.core.app.OpenCodeClient"), \
             patch("opencode_on_im.core.app.EventSubscriber"):
            return Application(settings)

    @pytest.mark.asyncio
    async def test_init(self, settings):
        app = Application(settings)
        assert app.settings == settings
        assert app.adapters == []
        assert not app._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_shutdown_signals_event(self, app):
        assert not app._shutdown_event.is_set()
        await app.shutdown()
        assert app._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_init_adapters_telegram(self, app):
        app.settings.telegram.token = "test_token"

        with patch("opencode_on_im.adapters.telegram.TelegramAdapter") as mock_adapter:
            await app._init_adapters()
            assert len(app.adapters) == 1
            mock_adapter.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_adapters_dingtalk(self, app):
        app.settings.dingtalk.app_key = "test_key"

        with patch("opencode_on_im.adapters.dingtalk.DingTalkAdapter") as mock_adapter:
            await app._init_adapters()
            assert len(app.adapters) == 1
            mock_adapter.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_services(self, app):
        mock_adapter = AsyncMock()
        app.adapters.append(mock_adapter)
        app.event_subscriber.start = AsyncMock()

        await app._start_services()

        mock_adapter.start.assert_awaited_once()
        app.event_subscriber.start.assert_awaited_once_with(app._on_opencode_event)

    @pytest.mark.asyncio
    async def test_stop_services(self, app):
        mock_adapter = AsyncMock()
        app.adapters.append(mock_adapter)
        app.event_subscriber.stop = AsyncMock()

        await app._stop_services()

        app.event_subscriber.stop.assert_awaited_once()
        mock_adapter.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_on_opencode_event(self, app):
        mock_event = MagicMock()
        mock_event.type = "test_event"
        mock_event.session_id = "test_session"
        mock_event.content = "test_content"
        mock_event.data = {"extra": "data"}

        app.adapters = [MagicMock()]
        app.notification_router.route = AsyncMock()

        await app._on_opencode_event(mock_event)

        app.notification_router.route.assert_awaited_once()
        args = app.notification_router.route.await_args[0]
        event_dict = args[0]

        assert event_dict["type"] == "test_event"
        assert event_dict["instance_id"] == "test_session"
        assert event_dict["content"] == "test_content"
        assert event_dict["extra"] == "data"

    @pytest.mark.asyncio
    async def test_run_cycle(self, app):
        # Mock run flow to avoid infinite wait
        app._shutdown_event.wait = AsyncMock()

        # Mock init/start/stop methods
        app._init_adapters = AsyncMock()
        app._start_services = AsyncMock()
        app._stop_services = AsyncMock()
        app._check_upgrade = AsyncMock()

        await app.run()

        app._check_upgrade.assert_awaited_once()
        app._init_adapters.assert_awaited_once()
        app._start_services.assert_awaited_once()
        app._shutdown_event.wait.assert_awaited_once()
        app._stop_services.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_check_upgrade_disabled(self, app):
        app.settings.upgrade_check_enabled = False
        with patch("opencode_on_im.utils.upgrade.check_upgrade") as mock_check:
            await app._check_upgrade()
            mock_check.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_upgrade_enabled(self, app):
        app.settings.upgrade_check_enabled = True
        with patch("opencode_on_im.utils.upgrade.check_upgrade", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = {"update_available": True, "latest_version": "1.0.0"}
            await app._check_upgrade()
            mock_check.assert_awaited_once()
