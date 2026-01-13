from typing import Any

import httpx
import structlog

from opencode_on_im.core.config import Settings

logger = structlog.get_logger()


class OpenCodeClient:

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = f"http://{settings.opencode_host}:{settings.opencode_port}"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def create_session(self, title: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post("/session", json={"title": title})
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data

    async def send_message(
        self,
        session_id: str,
        content: str,
        attachments: list[bytes] | None = None,
    ) -> dict[str, Any]:
        client = await self._get_client()

        payload: dict[str, Any] = {"content": content}
        if attachments:
            payload["attachments"] = attachments

        response = await client.post(f"/session/{session_id}/message", json=payload)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data

    async def get_session_status(self, session_id: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(f"/session/{session_id}")
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data

    async def cancel_task(self, session_id: str) -> None:
        client = await self._get_client()
        response = await client.post(f"/session/{session_id}/cancel")
        response.raise_for_status()

    async def list_sessions(self) -> list[dict[str, Any]]:
        client = await self._get_client()
        response = await client.get("/session")
        response.raise_for_status()
        data: list[dict[str, Any]] = response.json()
        return data
