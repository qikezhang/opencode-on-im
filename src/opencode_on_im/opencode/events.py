import asyncio
import contextlib
from collections.abc import Callable
from typing import Any

import httpx
import structlog

from opencode_on_im.opencode.client import OpenCodeClient

logger = structlog.get_logger()


class EventSubscriber:

    def __init__(self, client: OpenCodeClient) -> None:
        self.client = client
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self, callback: Callable[[dict[str, Any]], Any]) -> None:
        self._running = True
        self._task = asyncio.create_task(self._subscribe_loop(callback))
        logger.info("event_subscriber_started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("event_subscriber_stopped")

    async def _subscribe_loop(self, callback: Callable[[dict[str, Any]], Any]) -> None:
        while self._running:
            try:
                await self._subscribe(callback)
            except httpx.HTTPError as e:
                logger.warning("event_subscription_error", error=str(e))
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("event_subscription_failed", error=str(e))
                await asyncio.sleep(5)

    async def _subscribe(self, callback: Callable[[dict[str, Any]], Any]) -> None:
        import json

        base_url = self.client.base_url

        async with httpx.AsyncClient() as client, client.stream(
            "GET", f"{base_url}/event/subscribe"
        ) as response:
            async for line in response.aiter_lines():
                if not self._running:
                    break

                if line.startswith("data:"):
                    try:
                        event = json.loads(line[5:].strip())
                        await callback(event)
                    except json.JSONDecodeError:
                        logger.warning("invalid_event_data", line=line)
