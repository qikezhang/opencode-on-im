"""Main application orchestrator."""

import asyncio
from typing import TYPE_CHECKING, Any

import structlog

from opencode_on_im.core.config import Settings
from opencode_on_im.core.instance import InstanceRegistry
from opencode_on_im.core.notification import NotificationRouter
from opencode_on_im.core.session import SessionManager
from opencode_on_im.opencode.client import OpenCodeClient
from opencode_on_im.opencode.events import EventSubscriber, OpenCodeEvent

if TYPE_CHECKING:
    from opencode_on_im.adapters.base import BaseAdapter

logger = structlog.get_logger()


class Application:
    """Main application that orchestrates all components."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.adapters: list[BaseAdapter] = []
        self.session_manager = SessionManager(settings)
        self.instance_registry = InstanceRegistry(settings)
        self.notification_router = NotificationRouter()
        self.opencode_client = OpenCodeClient(settings)
        self.event_subscriber = EventSubscriber(self.opencode_client)
        self._shutdown_event = asyncio.Event()

    async def run(self) -> None:
        """Start all services and run until shutdown."""
        await self._check_upgrade()
        await self._init_adapters()
        await self._start_services()

        logger.info("application_started", adapters=len(self.adapters))

        await self._shutdown_event.wait()

        await self._stop_services()
        logger.info("application_stopped")

    async def shutdown(self) -> None:
        """Signal shutdown."""
        self._shutdown_event.set()

    async def _check_upgrade(self) -> None:
        """Check for available upgrades."""
        if not self.settings.upgrade_check_enabled:
            return

        try:
            from opencode_on_im.utils.upgrade import check_upgrade
            result = await check_upgrade(self.settings)
            if result and result.get("update_available"):
                logger.info(
                    "upgrade_available",
                    latest=result.get("latest_version"),
                    url=result.get("release_notes_url"),
                )
                if promo := result.get("promotion"):
                    logger.info("promotion", message=promo.get("message"))
        except Exception as e:
            logger.warning("upgrade_check_failed", error=str(e))

    async def _init_adapters(self) -> None:
        """Initialize enabled IM adapters."""
        if self.settings.telegram.token:
            from opencode_on_im.adapters.telegram import TelegramAdapter
            telegram_adapter = TelegramAdapter(
                self.settings,
                self.session_manager,
                self.instance_registry,
                self.notification_router,
            )
            self.adapters.append(telegram_adapter)
            logger.info("adapter_initialized", platform="telegram")

        if self.settings.dingtalk.app_key:
            from opencode_on_im.adapters.dingtalk import DingTalkAdapter
            dingtalk_adapter = DingTalkAdapter(
                self.settings,
                self.session_manager,
                self.instance_registry,
                self.notification_router,
            )
            self.adapters.append(dingtalk_adapter)
            logger.info("adapter_initialized", platform="dingtalk")

        if not self.adapters:
            logger.warning("no_adapters_configured")

    async def _start_services(self) -> None:
        """Start all adapters and event subscriber."""
        for adapter in self.adapters:
            await adapter.start()

        await self.event_subscriber.start(self._on_opencode_event)

    async def _stop_services(self) -> None:
        """Stop all services gracefully."""
        await self.event_subscriber.stop()

        for adapter in self.adapters:
            await adapter.stop()

    async def _on_opencode_event(self, event: OpenCodeEvent) -> None:
        """Handle events from OpenCode."""
        # Convert OpenCodeEvent to dict for notification router
        event_dict: dict[str, Any] = {
            "type": event.type,
            "instance_id": event.session_id,  # Map session to instance
            "content": event.content,
            **(event.data or {}),
        }
        await self.notification_router.route(event_dict, self.adapters)
