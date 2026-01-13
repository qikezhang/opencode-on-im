"""OpenCode HTTP API client."""

from typing import Any
from dataclasses import dataclass
import base64

import httpx
import structlog

from opencode_on_im.core.config import Settings

logger = structlog.get_logger()


@dataclass
class MessagePart:
    """A part of a message (text, image, or file)."""

    type: str  # "text", "image", "file"
    text: str | None = None
    media_type: str | None = None  # for image: "image/png", etc.
    data: str | None = None  # base64 encoded data for images


class OpenCodeClient:
    """Client for OpenCode HTTP API.

    OpenCode exposes a REST API at http://localhost:4096 by default.
    Key endpoints:
    - GET /global/health: Server health check
    - GET /session: List sessions
    - POST /session: Create session
    - POST /session/{id}/message: Send message (blocking)
    - POST /session/{id}/prompt_async: Send message (async, use SSE)
    - POST /session/{id}/abort: Cancel current task
    - GET /event or /global/event: SSE event stream
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = f"http://{settings.opencode_host}:{settings.opencode_port}"
        self._client: httpx.AsyncClient | None = None

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

    async def health_check(self) -> dict[str, Any]:
        """Check server health and get version info."""
        client = await self._get_client()
        response = await client.get("/global/health")
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        logger.debug("health_check", status="ok", data=data)
        return data

    async def is_available(self) -> bool:
        """Check if OpenCode server is available."""
        try:
            await self.health_check()
            return True
        except Exception as e:
            logger.debug("opencode_unavailable", error=str(e))
            return False

    # Session Management

    async def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions."""
        client = await self._get_client()
        response = await client.get("/session")
        response.raise_for_status()
        data: list[dict[str, Any]] = response.json()
        return data

    async def create_session(self, title: str | None = None) -> dict[str, Any]:
        """Create a new session."""
        client = await self._get_client()
        payload: dict[str, Any] = {}
        if title:
            payload["title"] = title

        response = await client.post("/session", json=payload)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        logger.info("session_created", session_id=data.get("id"))
        return data

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Get session details."""
        client = await self._get_client()
        response = await client.get(f"/session/{session_id}")
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data

    async def fork_session(
        self, session_id: str, message_id: str
    ) -> dict[str, Any]:
        """Fork a session at a specific message."""
        client = await self._get_client()
        response = await client.post(
            f"/session/{session_id}/fork",
            json={"messageID": message_id},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        logger.info("session_forked", old_id=session_id, new_id=data.get("id"))
        return data

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
        """
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

                parts.append({
                    "type": "image",
                    "mediaType": media_type,
                    "data": base64.b64encode(img_data).decode(),
                })

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

    async def send_message_async(
        self,
        session_id: str,
        text: str,
        images: list[bytes] | None = None,
    ) -> dict[str, Any]:
        """Send a message without waiting for response (async).

        Use SSE event stream to get the response.
        """
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

                parts.append({
                    "type": "image",
                    "mediaType": media_type,
                    "data": base64.b64encode(img_data).decode(),
                })

        response = await client.post(
            f"/session/{session_id}/prompt_async",
            json={"parts": parts},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        logger.debug("async_message_sent", session_id=session_id)
        return data

    async def abort_task(self, session_id: str) -> None:
        """Cancel/abort the current AI task in a session."""
        client = await self._get_client()
        response = await client.post(f"/session/{session_id}/abort")
        response.raise_for_status()
        logger.info("task_aborted", session_id=session_id)

    async def run_command(
        self, session_id: str, command: str
    ) -> dict[str, Any]:
        """Execute a slash command (e.g., /refactor, /test)."""
        client = await self._get_client()
        response = await client.post(
            f"/session/{session_id}/command",
            json={"command": command},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        logger.debug("command_executed", session_id=session_id, command=command)
        return data

    async def run_shell(
        self, session_id: str, command: str
    ) -> dict[str, Any]:
        """Run a shell command in the session context."""
        client = await self._get_client()
        response = await client.post(
            f"/session/{session_id}/shell",
            json={"command": command},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data

    # File Operations

    async def find_files(self, pattern: str) -> list[dict[str, Any]]:
        """Search for files matching a pattern."""
        client = await self._get_client()
        response = await client.get("/find", params={"pattern": pattern})
        response.raise_for_status()
        data: list[dict[str, Any]] = response.json()
        return data

    async def read_file(self, path: str) -> str:
        """Read file content."""
        client = await self._get_client()
        response = await client.get("/file/content", params={"path": path})
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        content: str = data.get("content", "")
        return content

    # TUI Control (for integration with running TUI)

    async def append_to_prompt(self, text: str) -> None:
        """Append text to the TUI input field."""
        client = await self._get_client()
        response = await client.post("/tui/append-prompt", json={"text": text})
        response.raise_for_status()

    async def submit_prompt(self) -> None:
        """Submit the current TUI prompt (simulate Enter key)."""
        client = await self._get_client()
        response = await client.post("/tui/submit-prompt")
        response.raise_for_status()
