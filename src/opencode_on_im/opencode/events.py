"""OpenCode SSE event subscriber."""

import asyncio
import contextlib
import json
from collections.abc import Callable, Awaitable
from dataclasses import dataclass
from typing import Any
from enum import Enum

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

    # Error events
    ERROR = "error"


@dataclass
class OpenCodeEvent:
    """Parsed OpenCode event."""

    type: str
    session_id: str | None = None
    message_id: str | None = None
    content: str | None = None
    data: dict[str, Any] | None = None

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


EventCallback = Callable[[OpenCodeEvent], Awaitable[None]]


class EventSubscriber:
    """Subscribes to OpenCode SSE event stream.

    OpenCode exposes SSE at:
    - GET /event: Session-specific events
    - GET /global/event: Global events (all sessions)

    Event format:
    data: {"type": "part.updated", "sessionID": "...", "content": "..."}
    """

    def __init__(self, client: OpenCodeClient) -> None:
        self.client = client
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 30.0

    async def start(self, callback: EventCallback) -> None:
        """Start subscribing to events."""
        self._running = True
        self._reconnect_delay = 1.0
        self._task = asyncio.create_task(self._subscribe_loop(callback))
        logger.info("event_subscriber_started", base_url=self.client.base_url)

    async def stop(self) -> None:
        """Stop subscribing to events."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("event_subscriber_stopped")

    @property
    def is_running(self) -> bool:
        """Check if subscriber is running."""
        return self._running

    async def _subscribe_loop(self, callback: EventCallback) -> None:
        """Main subscription loop with auto-reconnect."""
        while self._running:
            try:
                await self._subscribe(callback)
                # If we exit cleanly, reset delay
                self._reconnect_delay = 1.0
            except httpx.HTTPError as e:
                logger.warning(
                    "event_subscription_http_error",
                    error=str(e),
                    reconnect_in=self._reconnect_delay,
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "event_subscription_error",
                    error=str(e),
                    reconnect_in=self._reconnect_delay,
                )

            if self._running:
                await asyncio.sleep(self._reconnect_delay)
                # Exponential backoff
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self._max_reconnect_delay,
                )

    async def _subscribe(self, callback: EventCallback) -> None:
        """Subscribe to SSE stream."""
        base_url = self.client.base_url

        # Get auth if configured
        auth = None
        password = getattr(self.client.settings, "opencode_password", None)
        if password:
            auth = httpx.BasicAuth("opencode", password)

        async with httpx.AsyncClient(auth=auth, timeout=None) as client:
            # Use global event stream to get all events
            async with client.stream(
                "GET",
                f"{base_url}/global/event",
                headers={"Accept": "text/event-stream"},
            ) as response:
                response.raise_for_status()
                logger.debug("sse_connected", url=f"{base_url}/global/event")

                # Reset reconnect delay on successful connection
                self._reconnect_delay = 1.0

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

                logger.debug(
                    "event_received",
                    event_type=event.type,
                    session_id=event.session_id,
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
                self._reconnect_delay = retry_ms / 1000.0
            except ValueError:
                pass


class SessionEventSubscriber:
    """Subscribe to events for a specific session."""

    def __init__(self, client: OpenCodeClient, session_id: str) -> None:
        self.client = client
        self.session_id = session_id
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self, callback: EventCallback) -> None:
        """Start subscribing to session events."""
        self._running = True
        self._task = asyncio.create_task(self._subscribe_loop(callback))
        logger.info("session_subscriber_started", session_id=self.session_id)

    async def stop(self) -> None:
        """Stop subscribing."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _subscribe_loop(self, callback: EventCallback) -> None:
        """Subscription loop for single session."""
        while self._running:
            try:
                await self._subscribe(callback)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("session_subscribe_error", error=str(e))
                if self._running:
                    await asyncio.sleep(5)

    async def _subscribe(self, callback: EventCallback) -> None:
        """Subscribe to session-specific events."""
        base_url = self.client.base_url

        auth = None
        password = getattr(self.client.settings, "opencode_password", None)
        if password:
            auth = httpx.BasicAuth("opencode", password)

        async with httpx.AsyncClient(auth=auth, timeout=None) as client:
            async with client.stream(
                "GET",
                f"{base_url}/event",
                params={"sessionID": self.session_id},
                headers={"Accept": "text/event-stream"},
            ) as response:
                response.raise_for_status()

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
