from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from opencode_on_im.core.config import Settings
from opencode_on_im.core.instance import InstanceRegistry
from opencode_on_im.core.notification import NotificationRouter
from opencode_on_im.core.session import SessionManager


@dataclass
class IncomingMessage:
    platform: str
    user_id: str
    chat_id: str
    text: str
    voice_data: bytes | None = None
    reply_to_message_id: str | None = None


class BaseAdapter(ABC):
    def __init__(
        self,
        settings: Settings,
        session_manager: SessionManager,
        instance_registry: InstanceRegistry,
        notification_router: NotificationRouter,
    ) -> None:
        self.settings = settings
        self.session_manager = session_manager
        self.instance_registry = instance_registry
        self.notification_router = notification_router

    @property
    @abstractmethod
    def platform(self) -> str:
        pass

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def send_text(
        self,
        user_id: str,
        text: str,
        parse_mode: str | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def send_image(
        self,
        user_id: str,
        image: bytes,
        caption: str | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def send_card(
        self,
        user_id: str,
        title: str,
        content: str,
        buttons: list[dict[str, Any]],
    ) -> None:
        pass

    @abstractmethod
    async def send_event(self, user_id: str, event: dict[str, Any]) -> None:
        pass
