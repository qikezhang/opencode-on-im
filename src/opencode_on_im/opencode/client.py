"""OpenCode HTTP API client with retry logic.

Provides reliable communication with OpenCode server including:
- Automatic retries with exponential backoff
- Connection health monitoring
- Graceful degradation on failures
"""

import base64
import logging
from dataclasses import dataclass
from typing import Any

import httpx
import structlog
from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from opencode_on_im.core.config import Settings

logger = structlog.get_logger()

# Retry configuration
MAX_RETRIES = 3
MIN_WAIT_SECONDS = 1
MAX_WAIT_SECONDS = 10

# Exceptions that should trigger retry
RETRIABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
)


def create_retry_decorator(
    max_attempts: int = MAX_RETRIES,
    min_wait: float = MIN_WAIT_SECONDS,
    max_wait: float = MAX_WAIT_SECONDS,
):
    """Create a tenacity retry decorator with standard settings."""
    return retry(
        retry=retry_if_exception_type(RETRIABLE_EXCEPTIONS),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


# Standard retry decorator for API calls
api_retry = create_retry_decorator()


@dataclass
class MessagePart:
    """A part of a message (text, image, or file)."""

    type: str  # "text", "image", "file"
    text: str | None = None
    media_type: str | None = None  # for image: "image/png", etc.
    data: str | None = None  # base64 encoded data for images


class OpenCodeClient:
    """Client for OpenCode HTTP API with automatic retry.

    OpenCode exposes a REST API at http://localhost:4096 by default.
    Key endpoints:
    - GET /global/health: Server health check
    - GET /session: List sessions
    - POST /session: Create session
    - POST /session/{id}/message: Send message (blocking)
    - POST /session/{id}/prompt_async: Send message (async, use SSE)
    - POST /session/{id}/abort: Cancel current task
    - GET /event or /global/event: SSE event stream

    All API calls include automatic retry with exponential backoff
    for transient network failures.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = f"http://{settings.opencode_host}:{settings.opencode_port}"
        self._client: httpx.AsyncClient | None = None
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            # Check if password auth is needed
            auth = None
            password = getattr(self.settings, "opencode_password", None)
            if password:
                auth = httpx.BasicAuth("opencode", password)

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=60.0,
                auth=auth,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _record_success(self) -> None:
        """Record successful API call."""
        self._consecutive_failures = 0

    def _record_failure(self) -> None:
        """Record failed API call."""
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._max_consecutive_failures:
            logger.warning(
                "consecutive_failures_threshold",
                count=self._consecutive_failures,
                threshold=self._max_consecutive_failures,
            )

    @property
    def is_healthy(self) -> bool:
        """Check if client is in healthy state based on recent failures."""
        return self._consecutive_failures < self._max_consecutive_failures

    @api_retry
    async def health_check(self) -> dict[str, Any]:
        """Check server health and get version info."""
        try:
            client = await self._get_client()
            response = await client.get("/global/health")
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            logger.debug("health_check", status="ok", data=data)
            self._record_success()
            return data
        except Exception:
            self._record_failure()
            raise

    async def is_available(self) -> bool:
        """Check if OpenCode server is available."""
        try:
            await self.health_check()
            return True
        except (RetryError, *RETRIABLE_EXCEPTIONS) as e:
            logger.debug("opencode_unavailable", error=str(e))
            return False
        except Exception as e:
            logger.debug("opencode_unavailable", error=str(e))
            return False

    # Session Management

    @api_retry
    async def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions."""
        try:
            client = await self._get_client()
            response = await client.get("/session")
            response.raise_for_status()
            data: list[dict[str, Any]] = response.json()
            self._record_success()
            return data
        except Exception:
            self._record_failure()
            raise

    @api_retry
    async def create_session(self, title: str | None = None) -> dict[str, Any]:
        """Create a new session."""
        try:
            client = await self._get_client()
            payload: dict[str, Any] = {}
            if title:
                payload["title"] = title

            response = await client.post("/session", json=payload)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            logger.info("session_created", session_id=data.get("id"))
            self._record_success()
            return data
        except Exception:
            self._record_failure()
            raise

    @api_retry
    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Get session details."""
        try:
            client = await self._get_client()
            response = await client.get(f"/session/{session_id}")
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            self._record_success()
            return data
        except Exception:
            self._record_failure()
            raise

    @api_retry
    async def fork_session(self, session_id: str, message_id: str) -> dict[str, Any]:
        """Fork a session at a specific message."""
        try:
            client = await self._get_client()
            response = await client.post(
                f"/session/{session_id}/fork",
                json={"messageID": message_id},
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            logger.info("session_forked", old_id=session_id, new_id=data.get("id"))
            self._record_success()
            return data
        except Exception:
            self._record_failure()
            raise

    # Messaging

    async def send_message(
        self,
        session_id: str,
        text: str,
        images: list[bytes] | None = None,
        model_provider: str | None = None,
        model_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a message and wait for response (blocking).

        Args:
            session_id: Target session ID
            text: Message text
            images: Optional list of image bytes (PNG/JPEG)
            model_provider: Optional model provider (e.g., "anthropic")
            model_id: Optional model ID (e.g., "claude-3-5-sonnet-latest")

        Returns:
            Complete response including AI reply

        Note:
            This method uses custom retry logic with longer timeouts
            since AI responses can take significant time.
        """

        # Custom retry for long-running message sends
        @retry(
            retry=retry_if_exception_type((httpx.ReadTimeout, httpx.ConnectError)),
            stop=stop_after_attempt(2),  # Fewer retries for long operations
            wait=wait_exponential(multiplier=2, min=5, max=30),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        async def _send() -> dict[str, Any]:
            client = await self._get_client()

            # Build message parts
            parts: list[dict[str, Any]] = [{"type": "text", "text": text}]

            if images:
                for img_data in images:
                    # Detect image type from magic bytes
                    if img_data[:8] == b"\x89PNG\r\n\x1a\n":
                        media_type = "image/png"
                    elif img_data[:2] == b"\xff\xd8":
                        media_type = "image/jpeg"
                    else:
                        media_type = "image/png"  # default

                    parts.append(
                        {
                            "type": "image",
                            "mediaType": media_type,
                            "data": base64.b64encode(img_data).decode(),
                        }
                    )

            payload: dict[str, Any] = {"parts": parts}

            # Add model config if specified
            if model_provider and model_id:
                payload["model"] = {
                    "providerID": model_provider,
                    "modelID": model_id,
                }

            response = await client.post(
                f"/session/{session_id}/message",
                json=payload,
                timeout=300.0,  # Long timeout for AI responses
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            logger.debug("message_sent", session_id=session_id, response_id=data.get("id"))
            return data

        try:
            result = await _send()
            self._record_success()
            return result
        except Exception:
            self._record_failure()
            raise

    @api_retry
    async def send_message_async(
        self,
        session_id: str,
        text: str,
        images: list[bytes] | None = None,
    ) -> dict[str, Any]:
        """Send a message without waiting for response (async).

        Use SSE event stream to get the response.
        """
        try:
            client = await self._get_client()

            parts: list[dict[str, Any]] = [{"type": "text", "text": text}]

            if images:
                for img_data in images:
                    if img_data[:8] == b"\x89PNG\r\n\x1a\n":
                        media_type = "image/png"
                    elif img_data[:2] == b"\xff\xd8":
                        media_type = "image/jpeg"
                    else:
                        media_type = "image/png"

                    parts.append(
                        {
                            "type": "image",
                            "mediaType": media_type,
                            "data": base64.b64encode(img_data).decode(),
                        }
                    )

            response = await client.post(
                f"/session/{session_id}/prompt_async",
                json={"parts": parts},
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            logger.debug("async_message_sent", session_id=session_id)
            self._record_success()
            return data
        except Exception:
            self._record_failure()
            raise

    @api_retry
    async def abort_task(self, session_id: str) -> None:
        """Cancel/abort the current AI task in a session."""
        try:
            client = await self._get_client()
            response = await client.post(f"/session/{session_id}/abort")
            response.raise_for_status()
            logger.info("task_aborted", session_id=session_id)
            self._record_success()
        except Exception:
            self._record_failure()
            raise

    @api_retry
    async def run_command(self, session_id: str, command: str) -> dict[str, Any]:
        """Execute a slash command (e.g., /refactor, /test)."""
        try:
            client = await self._get_client()
            response = await client.post(
                f"/session/{session_id}/command",
                json={"command": command},
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            logger.debug("command_executed", session_id=session_id, command=command)
            self._record_success()
            return data
        except Exception:
            self._record_failure()
            raise

    @api_retry
    async def run_shell(self, session_id: str, command: str) -> dict[str, Any]:
        """Run a shell command in the session context."""
        try:
            client = await self._get_client()
            response = await client.post(
                f"/session/{session_id}/shell",
                json={"command": command},
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            self._record_success()
            return data
        except Exception:
            self._record_failure()
            raise

    # File Operations

    @api_retry
    async def find_files(self, pattern: str) -> list[dict[str, Any]]:
        """Search for files matching a pattern."""
        try:
            client = await self._get_client()
            response = await client.get("/find", params={"pattern": pattern})
            response.raise_for_status()
            data: list[dict[str, Any]] = response.json()
            self._record_success()
            return data
        except Exception:
            self._record_failure()
            raise

    @api_retry
    async def read_file(self, path: str) -> str:
        """Read file content."""
        try:
            client = await self._get_client()
            response = await client.get("/file/content", params={"path": path})
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            content: str = data.get("content", "")
            self._record_success()
            return content
        except Exception:
            self._record_failure()
            raise

    # TUI Control (for integration with running TUI)

    @api_retry
    async def append_to_prompt(self, text: str) -> None:
        """Append text to the TUI input field."""
        try:
            client = await self._get_client()
            response = await client.post("/tui/append-prompt", json={"text": text})
            response.raise_for_status()
            self._record_success()
        except Exception:
            self._record_failure()
            raise

    @api_retry
    async def submit_prompt(self) -> None:
        """Submit the current TUI prompt (simulate Enter key)."""
        try:
            client = await self._get_client()
            response = await client.post("/tui/submit-prompt")
            response.raise_for_status()
            self._record_success()
        except Exception:
            self._record_failure()
            raise
