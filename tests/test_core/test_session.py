"""Tests for SessionManager."""

import pytest
from pathlib import Path
import tempfile

from opencode_on_im.core.config import Settings
from opencode_on_im.core.session import SessionManager


@pytest.fixture
def temp_settings():
    """Create settings with temporary data directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Settings(data_dir=Path(tmpdir))


@pytest.fixture
async def session_manager(temp_settings):
    """Create and initialize a SessionManager."""
    manager = SessionManager(temp_settings)
    await manager.initialize()
    yield manager
    await manager.close()


class TestSessionManager:
    """Tests for SessionManager class."""

    async def test_initialize_creates_database(self, temp_settings):
        """Test that initialize creates the database file."""
        manager = SessionManager(temp_settings)
        await manager.initialize()

        assert manager.db_path.exists()
        await manager.close()

    async def test_bind_user_success(self, session_manager):
        """Test binding a user to an instance."""
        result = await session_manager.bind_user(
            platform="telegram",
            user_id="123456",
            instance_id="instance-abc",
        )

        assert result is True

    async def test_bind_user_duplicate_updates_last_active(self, session_manager):
        """Test that binding same user twice updates last_active."""
        await session_manager.bind_user("telegram", "123", "inst-1")
        result = await session_manager.bind_user("telegram", "123", "inst-1")

        assert result is True

    async def test_get_user_instances(self, session_manager):
        """Test getting all instances for a user."""
        await session_manager.bind_user("telegram", "user1", "inst-a")
        await session_manager.bind_user("telegram", "user1", "inst-b")
        await session_manager.bind_user("telegram", "user2", "inst-c")

        instances = await session_manager.get_user_instances("telegram", "user1")

        assert len(instances) == 2
        assert "inst-a" in instances
        assert "inst-b" in instances

    async def test_get_instance_users(self, session_manager):
        """Test getting all users for an instance."""
        await session_manager.bind_user("telegram", "user1", "shared-inst")
        await session_manager.bind_user("telegram", "user2", "shared-inst")
        await session_manager.bind_user("dingtalk", "user3", "shared-inst")

        users = await session_manager.get_instance_users("shared-inst")

        assert len(users) == 3
        assert ("telegram", "user1") in users
        assert ("telegram", "user2") in users
        assert ("dingtalk", "user3") in users

    async def test_unbind_user(self, session_manager):
        """Test unbinding a user from an instance."""
        await session_manager.bind_user("telegram", "user1", "inst-1")

        result = await session_manager.unbind_user("telegram", "user1", "inst-1")
        assert result is True

        instances = await session_manager.get_user_instances("telegram", "user1")
        assert len(instances) == 0

    async def test_unbind_nonexistent_returns_false(self, session_manager):
        """Test unbinding non-existent binding returns False."""
        result = await session_manager.unbind_user("telegram", "nobody", "nothing")
        assert result is False

    async def test_save_and_get_offline_messages(self, session_manager):
        """Test saving and retrieving offline messages."""
        await session_manager.save_offline_message(
            instance_id="inst-1",
            platform="telegram",
            user_id="user1",
            content="Hello offline!",
        )
        await session_manager.save_offline_message(
            instance_id="inst-1",
            platform="telegram",
            user_id="user1",
            content="Second message",
        )

        messages = await session_manager.get_offline_messages("telegram", "user1")

        assert len(messages) == 2
        assert messages[0]["content"] == "Hello offline!"
        assert messages[1]["content"] == "Second message"

    async def test_get_offline_messages_clears_them(self, session_manager):
        """Test that getting offline messages clears them."""
        await session_manager.save_offline_message(
            instance_id="inst-1",
            platform="telegram",
            user_id="user1",
            content="One time message",
        )

        # First retrieval
        messages = await session_manager.get_offline_messages("telegram", "user1")
        assert len(messages) == 1

        # Second retrieval should be empty
        messages = await session_manager.get_offline_messages("telegram", "user1")
        assert len(messages) == 0

    async def test_offline_messages_limit(self, temp_settings):
        """Test that offline messages respect max limit."""
        temp_settings.max_offline_messages = 3
        manager = SessionManager(temp_settings)
        await manager.initialize()

        # Save 5 messages
        for i in range(5):
            await manager.save_offline_message(
                instance_id="inst-1",
                platform="telegram",
                user_id="user1",
                content=f"Message {i}",
            )

        messages = await manager.get_offline_messages("telegram", "user1")

        # Should only have last 3
        assert len(messages) == 3
        assert messages[0]["content"] == "Message 2"
        assert messages[1]["content"] == "Message 3"
        assert messages[2]["content"] == "Message 4"

        await manager.close()
