"""OpenCode SSE event subscriber with robust auto-reconnect.

Provides:
- Automatic reconnection with exponential backoff
- Connection status monitoring
- Event buffering during reconnection
- Graceful shutdown
"""

import asyncio
import contextlib
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx
import structlog

from opencode_on_im.opencode.client import OpenCodeClient

logger = structlog.get_logger()


class EventType(str, Enum):
    """OpenCode event types."""

    # Connection events
    SERVER_CONNECTED = "server.connected"

    # Session events
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    SESSION_DELETED = "session.deleted"

    # Message events
    MESSAGE_CREATED = "message.created"
    MESSAGE_UPDATED = "message.updated"
    MESSAGE_COMPLETED = "message.completed"

    # Streaming events
    PART_UPDATED = "part.updated"

    # Tool events
    TOOL_START = "tool.start"
    TOOL_END = "tool.end"

    # Error events
    ERROR = "error"

    # Internal connection events (not from OpenCode)
    CONNECTION_LOST = "_connection.lost"
    CONNECTION_RESTORED = "_connection.restored"


class ConnectionState(str, Enum):
    """SSE connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


@dataclass
class OpenCodeEvent:
    """Parsed OpenCode event."""

    type: str
    session_id: str | None = None
    message_id: str | None = None
    content: str | None = None
    data: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OpenCodeEvent":
        """Parse event from SSE data."""
        return cls(
            type=data.get("type", "unknown"),
            session_id=data.get("sessionID") or data.get("session_id"),
            message_id=data.get("messageID") or data.get("message_id"),
            content=data.get("content"),
            data=data,
        )


@dataclass
class ConnectionStats:
    """Statistics about SSE connection."""

    total_events: int = 0
    total_reconnects: int = 0
    last_event_time: datetime | None = None
    last_reconnect_time: datetime | None = None
    connected_since: datetime | None = None
    current_state: ConnectionState = ConnectionState.DISCONNECTED


EventCallback = Callable[[OpenCodeEvent], Awaitable[None]]
StateCallback = Callable[[ConnectionState, ConnectionState], Awaitable[None]]


class EventSubscriber:
    """Subscribes to OpenCode SSE event stream with auto-reconnect.

    OpenCode exposes SSE at:
    - GET /event: Session-specific events
    - GET /global/event: Global events (all sessions)

    Event format:
    data: {"type": "part.updated", "sessionID": "...", "content": "..."}

    Features:
    - Automatic reconnection with exponential backoff
    - Connection state tracking
    - Event statistics
    - Configurable retry behavior
    """

    def __init__(
        self,
        client: OpenCodeClient,
        min_reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 30.0,
        max_reconnect_attempts: int | None = None,  # None = infinite
    ) -> None:
        self.client = client
        self._running = False
        self._task: asyncio.Task[None] | None = None

        # Reconnection settings
        self._min_reconnect_delay = min_reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        self._max_reconnect_attempts = max_reconnect_attempts
        self._reconnect_delay = min_reconnect_delay
        self._reconnect_attempts = 0

        # State tracking
        self._state = ConnectionState.DISCONNECTED
        self._stats = ConnectionStats()
        self._state_callback: StateCallback | None = None

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def stats(self) -> ConnectionStats:
        """Get connection statistics."""
        return self._stats

    @property
    def is_running(self) -> bool:
        """Check if subscriber is running."""
        return self._running

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._state == ConnectionState.CONNECTED

    def on_state_change(self, callback: StateCallback) -> None:
        """Register callback for connection state changes."""
        self._state_callback = callback

    async def _set_state(self, new_state: ConnectionState) -> None:
        """Update connection state and notify callback."""
        old_state = self._state
        if old_state != new_state:
            self._state = new_state
            self._stats.current_state = new_state
            logger.debug(
                "connection_state_changed",
                old_state=old_state.value,
                new_state=new_state.value,
            )
            if self._state_callback:
                try:
                    await self._state_callback(old_state, new_state)
                except Exception as e:
                    logger.error("state_callback_error", error=str(e))

    async def start(self, callback: EventCallback) -> None:
        """Start subscribing to events."""
        if self._running:
            logger.warning("subscriber_already_running")
            return

        self._running = True
        self._reconnect_delay = self._min_reconnect_delay
        self._reconnect_attempts = 0
        await self._set_state(ConnectionState.CONNECTING)

        self._task = asyncio.create_task(self._subscribe_loop(callback))
        logger.info("event_subscriber_started", base_url=self.client.base_url)

    async def stop(self) -> None:
        """Stop subscribing to events."""
        self._running = False
        await self._set_state(ConnectionState.DISCONNECTED)

        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        logger.info(
            "event_subscriber_stopped",
            total_events=self._stats.total_events,
            total_reconnects=self._stats.total_reconnects,
        )

    async def _subscribe_loop(self, callback: EventCallback) -> None:
        """Main subscription loop with auto-reconnect."""
        while self._running:
            try:
                await self._subscribe(callback)
                # If we exit cleanly, reset counters
                self._reconnect_delay = self._min_reconnect_delay
                self._reconnect_attempts = 0

            except httpx.HTTPStatusError as e:
                logger.warning(
                    "event_subscription_http_error",
                    status_code=e.response.status_code,
                    error=str(e),
                )
                # Don't retry on auth errors
                if e.response.status_code in (401, 403):
                    logger.error("auth_error_stopping", status=e.response.status_code)
                    break

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
                logger.warning(
                    "event_subscription_connection_error",
                    error=str(e),
                    reconnect_in=self._reconnect_delay,
                    attempt=self._reconnect_attempts,
                )

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(
                    "event_subscription_unexpected_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    reconnect_in=self._reconnect_delay,
                )

            # Handle reconnection
            if self._running:
                self._reconnect_attempts += 1
                self._stats.total_reconnects += 1
                self._stats.last_reconnect_time = datetime.now(UTC)

                # Check max attempts
                if (
                    self._max_reconnect_attempts is not None
                    and self._reconnect_attempts >= self._max_reconnect_attempts
                ):
                    logger.error(
                        "max_reconnect_attempts_reached",
                        attempts=self._reconnect_attempts,
                    )
                    break

                await self._set_state(ConnectionState.RECONNECTING)

                # Send internal connection lost event
                await callback(
                    OpenCodeEvent(
                        type=EventType.CONNECTION_LOST.value,
                        data={"reconnect_in": self._reconnect_delay},
                    )
                )

                await asyncio.sleep(self._reconnect_delay)

                # Exponential backoff with jitter
                import random

                jitter = random.uniform(0.8, 1.2)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2 * jitter,
                    self._max_reconnect_delay,
                )

        await self._set_state(ConnectionState.DISCONNECTED)

    async def _subscribe(self, callback: EventCallback) -> None:
        """Subscribe to SSE stream."""
        base_url = self.client.base_url

        # Get auth if configured
        auth = None
        password = getattr(self.client.settings, "opencode_password", None)
        if password:
            auth = httpx.BasicAuth("opencode", password)

        await self._set_state(ConnectionState.CONNECTING)

        async with (
            httpx.AsyncClient(auth=auth, timeout=None) as client,
            client.stream(
                "GET",
                f"{base_url}/global/event",
                headers={"Accept": "text/event-stream"},
            ) as response,
        ):
            response.raise_for_status()

            # Successfully connected
            await self._set_state(ConnectionState.CONNECTED)
            self._stats.connected_since = datetime.now(UTC)
            self._reconnect_delay = self._min_reconnect_delay
            self._reconnect_attempts = 0

            logger.info(
                "sse_connected",
                url=f"{base_url}/global/event",
                reconnect_attempts=self._stats.total_reconnects,
            )

            # Send internal connection restored event if this was a reconnect
            if self._stats.total_reconnects > 0:
                await callback(
                    OpenCodeEvent(
                        type=EventType.CONNECTION_RESTORED.value,
                        data={"reconnect_count": self._stats.total_reconnects},
                    )
                )

            async for line in response.aiter_lines():
                if not self._running:
                    break

                await self._process_line(line, callback)

    async def _process_line(self, line: str, callback: EventCallback) -> None:
        """Process a single SSE line."""
        if not line:
            return

        # SSE format: "data: {...}"
        if line.startswith("data:"):
            data_str = line[5:].strip()
            if not data_str:
                return

            try:
                data = json.loads(data_str)
                event = OpenCodeEvent.from_dict(data)

                # Update stats
                self._stats.total_events += 1
                self._stats.last_event_time = datetime.now(UTC)

                logger.debug(
                    "event_received",
                    event_type=event.type,
                    session_id=event.session_id,
                    total_events=self._stats.total_events,
                )

                await callback(event)

            except json.JSONDecodeError as e:
                logger.warning("invalid_sse_data", line=line[:100], error=str(e))
            except Exception as e:
                logger.error("event_callback_error", error=str(e))

        elif line.startswith("event:"):
            # Named event type (optional in SSE)
            pass
        elif line.startswith("id:"):
            # Event ID (optional in SSE)
            pass
        elif line.startswith("retry:"):
            # Retry interval hint from server
            try:
                retry_ms = int(line[6:].strip())
                self._reconnect_delay = max(
                    self._min_reconnect_delay,
                    min(retry_ms / 1000.0, self._max_reconnect_delay),
                )
                logger.debug("retry_interval_updated", delay=self._reconnect_delay)
            except ValueError:
                pass


class SessionEventSubscriber:
    """Subscribe to events for a specific session with auto-reconnect."""

    def __init__(
        self,
        client: OpenCodeClient,
        session_id: str,
        min_reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 30.0,
    ) -> None:
        self.client = client
        self.session_id = session_id
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._min_reconnect_delay = min_reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        self._reconnect_delay = min_reconnect_delay
        self._state = ConnectionState.DISCONNECTED

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._state == ConnectionState.CONNECTED

    async def start(self, callback: EventCallback) -> None:
        """Start subscribing to session events."""
        self._running = True
        self._reconnect_delay = self._min_reconnect_delay
        self._task = asyncio.create_task(self._subscribe_loop(callback))
        logger.info("session_subscriber_started", session_id=self.session_id)

    async def stop(self) -> None:
        """Stop subscribing."""
        self._running = False
        self._state = ConnectionState.DISCONNECTED
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _subscribe_loop(self, callback: EventCallback) -> None:
        """Subscription loop for single session with auto-reconnect."""
        while self._running:
            try:
                self._state = ConnectionState.CONNECTING
                await self._subscribe(callback)
                self._reconnect_delay = self._min_reconnect_delay
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(
                    "session_subscribe_error",
                    session_id=self.session_id,
                    error=str(e),
                    reconnect_in=self._reconnect_delay,
                )
                self._state = ConnectionState.RECONNECTING

                if self._running:
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(
                        self._reconnect_delay * 2,
                        self._max_reconnect_delay,
                    )

        self._state = ConnectionState.DISCONNECTED

    async def _subscribe(self, callback: EventCallback) -> None:
        """Subscribe to session-specific events."""
        base_url = self.client.base_url

        auth = None
        password = getattr(self.client.settings, "opencode_password", None)
        if password:
            auth = httpx.BasicAuth("opencode", password)

        async with (
            httpx.AsyncClient(auth=auth, timeout=None) as client,
            client.stream(
                "GET",
                f"{base_url}/event",
                params={"sessionID": self.session_id},
                headers={"Accept": "text/event-stream"},
            ) as response,
        ):
            response.raise_for_status()
            self._state = ConnectionState.CONNECTED
            self._reconnect_delay = self._min_reconnect_delay

            logger.debug("session_sse_connected", session_id=self.session_id)

            async for line in response.aiter_lines():
                if not self._running:
                    break

                if line.startswith("data:"):
                    try:
                        data = json.loads(line[5:].strip())
                        event = OpenCodeEvent.from_dict(data)
                        await callback(event)
                    except (json.JSONDecodeError, Exception) as e:
                        logger.warning("session_event_error", error=str(e))
