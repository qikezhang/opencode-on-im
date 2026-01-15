"""Tests for NotificationRouter."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from opencode_on_im.core.notification import NotificationRouter


@pytest.fixture
def router():
    """Create a NotificationRouter."""
    return NotificationRouter()


@pytest.fixture
def mock_adapter():
    """Create a mock adapter."""
    adapter = MagicMock()
    adapter.platform = "telegram"
    adapter.send_event = AsyncMock()
    adapter.send_text = AsyncMock()
    return adapter


class TestNotificationRouter:
    """Tests for NotificationRouter class."""

    def test_register_online(self, router):
        """Test registering a user as online."""
        router.register_online("inst-1", "telegram", "user1")

        users = router.get_online_users("inst-1")
        assert ("telegram", "user1") in users

    def test_register_multiple_users(self, router):
        """Test registering multiple users."""
        router.register_online("inst-1", "telegram", "user1")
        router.register_online("inst-1", "telegram", "user2")
        router.register_online("inst-1", "dingtalk", "user3")

        users = router.get_online_users("inst-1")
        assert len(users) == 3

    def test_unregister_online(self, router):
        """Test unregistering a user."""
        router.register_online("inst-1", "telegram", "user1")
        router.unregister_online("inst-1", "telegram", "user1")

        users = router.get_online_users("inst-1")
        assert len(users) == 0

    def test_get_online_users_empty_instance(self, router):
        """Test getting users for instance with no online users."""
        users = router.get_online_users("nonexistent")
        assert users == []

    def test_format_online_status(self, router):
        """Test formatting online status message."""
        router.register_online("inst-1", "telegram", "user1")
        router.register_online("inst-1", "telegram", "user2")

        status = router.format_online_status("inst-1")

        assert "user1" in status
        assert "user2" in status
        assert "📡" in status

    def test_format_online_status_exclude_user(self, router):
        """Test formatting excludes specified user."""
        router.register_online("inst-1", "telegram", "user1")
        router.register_online("inst-1", "telegram", "user2")

        status = router.format_online_status("inst-1", exclude_user=("telegram", "user1"))

        assert "user1" not in status
        assert "user2" in status

    def test_format_online_status_empty(self, router):
        """Test formatting when no users online."""
        status = router.format_online_status("inst-1")
        assert status == ""

    async def test_route_event(self, router, mock_adapter):
        """Test routing an event to online users."""
        router.register_online("inst-1", "telegram", "user1")

        event = {"type": "message", "instance_id": "inst-1", "content": "Hello"}
        await router.route(event, [mock_adapter])

        mock_adapter.send_event.assert_called_once_with("user1", event)

    async def test_route_event_no_instance_id(self, router, mock_adapter):
        """Test routing event without instance_id does nothing."""
        router.register_online("inst-1", "telegram", "user1")

        event = {"type": "message", "content": "Hello"}
        await router.route(event, [mock_adapter])

        mock_adapter.send_event.assert_not_called()

    async def test_route_event_multiple_users(self, router, mock_adapter):
        """Test routing to multiple users."""
        router.register_online("inst-1", "telegram", "user1")
        router.register_online("inst-1", "telegram", "user2")

        event = {"type": "message", "instance_id": "inst-1"}
        await router.route(event, [mock_adapter])

        assert mock_adapter.send_event.call_count == 2

    async def test_broadcast(self, router, mock_adapter):
        """Test broadcasting a message."""
        router.register_online("inst-1", "telegram", "user1")
        router.register_online("inst-1", "telegram", "user2")

        await router.broadcast("inst-1", "Hello everyone!", [mock_adapter])

        assert mock_adapter.send_text.call_count == 2

    async def test_broadcast_exclude_user(self, router, mock_adapter):
        """Test broadcasting excludes specified user."""
        router.register_online("inst-1", "telegram", "user1")
        router.register_online("inst-1", "telegram", "user2")

        await router.broadcast(
            "inst-1",
            "Hello!",
            [mock_adapter],
            exclude=("telegram", "user1"),
        )

        mock_adapter.send_text.assert_called_once_with("user2", "Hello!")

    async def test_route_handles_adapter_error(self, router, mock_adapter):
        """Test that route handles adapter errors gracefully."""
        router.register_online("inst-1", "telegram", "user1")
        mock_adapter.send_event.side_effect = Exception("Network error")

        event = {"type": "message", "instance_id": "inst-1"}
        # Should not raise
        await router.route(event, [mock_adapter])
