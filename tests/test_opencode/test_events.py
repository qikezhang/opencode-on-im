"""Tests for OpenCode events module."""

from datetime import datetime

from opencode_on_im.opencode.events import (
    ConnectionState,
    ConnectionStats,
    EventType,
    OpenCodeEvent,
)


class TestEventType:
    def test_event_types_exist(self):
        assert EventType.SERVER_CONNECTED == "server.connected"
        assert EventType.MESSAGE_CREATED == "message.created"
        assert EventType.TOOL_START == "tool.start"
        assert EventType.ERROR == "error"

    def test_internal_events(self):
        assert EventType.CONNECTION_LOST == "_connection.lost"
        assert EventType.CONNECTION_RESTORED == "_connection.restored"


class TestConnectionState:
    def test_states_exist(self):
        assert ConnectionState.DISCONNECTED == "disconnected"
        assert ConnectionState.CONNECTING == "connecting"
        assert ConnectionState.CONNECTED == "connected"
        assert ConnectionState.RECONNECTING == "reconnecting"


class TestOpenCodeEvent:
    def test_from_dict_basic(self):
        data = {"type": "message.created"}
        event = OpenCodeEvent.from_dict(data)
        assert event.type == "message.created"
        assert event.session_id is None

    def test_from_dict_with_session_id(self):
        data = {"type": "message.created", "sessionID": "abc123"}
        event = OpenCodeEvent.from_dict(data)
        assert event.session_id == "abc123"

    def test_from_dict_with_snake_case_session(self):
        data = {"type": "message.created", "session_id": "def456"}
        event = OpenCodeEvent.from_dict(data)
        assert event.session_id == "def456"

    def test_from_dict_with_content(self):
        data = {"type": "part.updated", "content": "Hello world"}
        event = OpenCodeEvent.from_dict(data)
        assert event.content == "Hello world"

    def test_from_dict_with_message_id(self):
        data = {"type": "message.updated", "messageID": "msg123"}
        event = OpenCodeEvent.from_dict(data)
        assert event.message_id == "msg123"

    def test_from_dict_stores_data(self):
        data = {"type": "custom", "extra_field": "value"}
        event = OpenCodeEvent.from_dict(data)
        assert event.data == data
        assert event.data["extra_field"] == "value"

    def test_timestamp_auto_generated(self):
        data = {"type": "test"}
        event = OpenCodeEvent.from_dict(data)
        assert isinstance(event.timestamp, datetime)

    def test_unknown_type_fallback(self):
        data = {}  # No type field
        event = OpenCodeEvent.from_dict(data)
        assert event.type == "unknown"


class TestConnectionStats:
    def test_default_values(self):
        stats = ConnectionStats()
        assert stats.total_events == 0
        assert stats.total_reconnects == 0
        assert stats.last_event_time is None
        assert stats.current_state == ConnectionState.DISCONNECTED

    def test_update_stats(self):
        stats = ConnectionStats()
        stats.total_events = 10
        stats.total_reconnects = 2
        stats.current_state = ConnectionState.CONNECTED

        assert stats.total_events == 10
        assert stats.total_reconnects == 2
        assert stats.current_state == ConnectionState.CONNECTED
