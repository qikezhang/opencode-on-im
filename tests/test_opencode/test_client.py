"""Tests for OpenCode client and events."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opencode_on_im.core.config import Settings
from opencode_on_im.opencode.client import OpenCodeClient
from opencode_on_im.opencode.events import (
    EventSubscriber,
    EventType,
    OpenCodeEvent,
)


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        opencode_host="127.0.0.1",
        opencode_port=4096,
    )


@pytest.fixture
def client(settings):
    """Create OpenCode client."""
    return OpenCodeClient(settings)


class TestOpenCodeClient:
    """Tests for OpenCodeClient."""

    async def test_client_init(self, client):
        """Test client initialization."""
        assert client.base_url == "http://127.0.0.1:4096"
        assert client._client is None

    async def test_close_without_init(self, client):
        """Test close when client not initialized."""
        await client.close()  # Should not raise

    @patch("httpx.AsyncClient")
    async def test_health_check(self, mock_client_class, client):
        """Test health check endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "version": "1.0.0"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Directly set the mock client
        client._client = mock_client

        result = await client.health_check()

        assert result["status"] == "ok"
        mock_client.get.assert_called_once_with("/global/health")

    @patch("httpx.AsyncClient")
    async def test_is_available_success(self, mock_client_class, client):
        """Test is_available when server responds."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_client

        result = await client.is_available()
        assert result is True

    @patch("httpx.AsyncClient")
    async def test_is_available_failure(self, mock_client_class, client):
        """Test is_available when server not responding."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        client._client = mock_client

        result = await client.is_available()
        assert result is False

    @patch("httpx.AsyncClient")
    async def test_create_session(self, mock_client_class, client):
        """Test session creation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "ses_123", "title": "Test"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        client._client = mock_client

        result = await client.create_session(title="Test")

        assert result["id"] == "ses_123"
        mock_client.post.assert_called_once()

    @patch("httpx.AsyncClient")
    async def test_send_message(self, mock_client_class, client):
        """Test sending a message."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "msg_123", "content": "Response"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        client._client = mock_client

        result = await client.send_message(
            session_id="ses_123",
            text="Hello AI",
        )

        assert result["id"] == "msg_123"
        call_args = mock_client.post.call_args
        assert "parts" in call_args.kwargs["json"]

    @patch("httpx.AsyncClient")
    async def test_send_message_with_image(self, mock_client_class, client):
        """Test sending a message with image."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "msg_123"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        client._client = mock_client

        # PNG magic bytes
        png_data = b"\x89PNG\r\n\x1a\n" + b"fake image data"

        await client.send_message(
            session_id="ses_123",
            text="What's in this image?",
            images=[png_data],
        )

        call_args = mock_client.post.call_args
        parts = call_args.kwargs["json"]["parts"]
        assert len(parts) == 2
        assert parts[0]["type"] == "text"
        assert parts[1]["type"] == "image"
        assert parts[1]["mediaType"] == "image/png"

    @patch("httpx.AsyncClient")
    async def test_abort_task(self, mock_client_class, client):
        """Test aborting a task."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        client._client = mock_client

        await client.abort_task("ses_123")

        mock_client.post.assert_called_once_with("/session/ses_123/abort")

    @patch("httpx.AsyncClient")
    async def test_list_sessions(self, mock_client_class, client):
        """Test listing sessions."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": "ses_1", "title": "Session 1"},
            {"id": "ses_2", "title": "Session 2"},
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_client

        result = await client.list_sessions()

        assert len(result) == 2
        mock_client.get.assert_called_once_with("/session")


class TestOpenCodeEvent:
    """Tests for OpenCodeEvent parsing."""

    def test_from_dict_basic(self):
        """Test parsing basic event."""
        data = {
            "type": "message.created",
            "sessionID": "ses_123",
            "messageID": "msg_456",
        }

        event = OpenCodeEvent.from_dict(data)

        assert event.type == "message.created"
        assert event.session_id == "ses_123"
        assert event.message_id == "msg_456"

    def test_from_dict_with_content(self):
        """Test parsing event with content."""
        data = {
            "type": "part.updated",
            "sessionID": "ses_123",
            "content": "Hello, I can help with that.",
        }

        event = OpenCodeEvent.from_dict(data)

        assert event.content == "Hello, I can help with that."
        assert event.data == data

    def test_from_dict_missing_fields(self):
        """Test parsing event with missing optional fields."""
        data = {"type": "server.connected"}

        event = OpenCodeEvent.from_dict(data)

        assert event.type == "server.connected"
        assert event.session_id is None
        assert event.message_id is None

    def test_event_type_enum(self):
        """Test EventType enum values."""
        assert EventType.SERVER_CONNECTED == "server.connected"
        assert EventType.MESSAGE_CREATED == "message.created"
        assert EventType.PART_UPDATED == "part.updated"


class TestEventSubscriber:
    """Tests for EventSubscriber."""

    async def test_subscriber_init(self, client):
        """Test subscriber initialization."""
        subscriber = EventSubscriber(client)

        assert subscriber._running is False
        assert subscriber._task is None

    async def test_subscriber_start_stop(self, client):
        """Test starting and stopping subscriber."""
        subscriber = EventSubscriber(client)

        callback = AsyncMock()

        # Start (will fail to connect, but that's ok for this test)
        await subscriber.start(callback)
        assert subscriber._running is True
        assert subscriber._task is not None

        # Stop
        await subscriber.stop()
        assert subscriber._running is False

    async def test_is_running_property(self, client):
        """Test is_running property."""
        subscriber = EventSubscriber(client)

        assert subscriber.is_running is False

        subscriber._running = True
        assert subscriber.is_running is True

    async def test_process_line_valid_data(self, client):
        """Test processing valid SSE data line."""
        subscriber = EventSubscriber(client)
        received_events = []

        async def callback(event: OpenCodeEvent) -> None:
            received_events.append(event)

        line = 'data: {"type": "message.created", "sessionID": "ses_123"}'
        await subscriber._process_line(line, callback)

        assert len(received_events) == 1
        assert received_events[0].type == "message.created"
        assert received_events[0].session_id == "ses_123"

    async def test_process_line_invalid_json(self, client):
        """Test processing invalid JSON in SSE data."""
        subscriber = EventSubscriber(client)
        callback = AsyncMock()

        line = "data: {invalid json}"
        await subscriber._process_line(line, callback)

        # Should not call callback on invalid JSON
        callback.assert_not_called()

    async def test_process_line_empty(self, client):
        """Test processing empty line."""
        subscriber = EventSubscriber(client)
        callback = AsyncMock()

        await subscriber._process_line("", callback)
        await subscriber._process_line("   ", callback)

        callback.assert_not_called()

    async def test_process_line_event_prefix(self, client):
        """Test processing event: prefix line."""
        subscriber = EventSubscriber(client)
        callback = AsyncMock()

        line = "event: message.created"
        await subscriber._process_line(line, callback)

        # event: lines are ignored (data: contains the payload)
        callback.assert_not_called()

    async def test_process_line_retry_prefix(self, client):
        """Test processing retry: prefix line."""
        subscriber = EventSubscriber(client)
        callback = AsyncMock()

        subscriber._reconnect_delay = 1.0
        line = "retry: 5000"
        await subscriber._process_line(line, callback)

        assert subscriber._reconnect_delay == 5.0
