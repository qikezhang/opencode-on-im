from typing import Any

import structlog

from opencode_on_im.adapters.base import BaseAdapter
from opencode_on_im.core.config import Settings
from opencode_on_im.core.instance import InstanceRegistry
from opencode_on_im.core.notification import NotificationRouter
from opencode_on_im.core.session import SessionManager

logger = structlog.get_logger()


class DingTalkAdapter(BaseAdapter):

    def __init__(
        self,
        settings: Settings,
        session_manager: SessionManager,
        instance_registry: InstanceRegistry,
        notification_router: NotificationRouter,
    ) -> None:
        super().__init__(settings, session_manager, instance_registry, notification_router)
        self._running = False

    @property
    def platform(self) -> str:
        return "dingtalk"

    async def start(self) -> None:
        logger.info("dingtalk_adapter_starting")
        self._running = True

    async def stop(self) -> None:
        logger.info("dingtalk_adapter_stopping")
        self._running = False

    async def send_text(
        self,
        user_id: str,
        text: str,
        parse_mode: str | None = None,  # noqa: ARG002
    ) -> None:
        logger.info("dingtalk_send_text", user_id=user_id, text_len=len(text))

    async def send_image(
        self,
        user_id: str,
        image: bytes,
        caption: str | None = None,  # noqa: ARG002
    ) -> None:
        logger.info("dingtalk_send_image", user_id=user_id, image_size=len(image))

    async def send_card(
        self,
        user_id: str,
        title: str,
        content: str,  # noqa: ARG002
        buttons: list[dict[str, Any]],  # noqa: ARG002
    ) -> None:
        logger.info("dingtalk_send_card", user_id=user_id, title=title)

    async def send_event(self, user_id: str, event: dict[str, Any]) -> None:
        event_type = event.get("type", "unknown")
        logger.info("dingtalk_send_event", user_id=user_id, event_type=event_type)
