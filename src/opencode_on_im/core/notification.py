"""Notification routing to multiple users/adapters."""

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from opencode_on_im.adapters.base import BaseAdapter

logger = structlog.get_logger()


class NotificationRouter:
    """Routes OpenCode events to appropriate IM users."""

    def __init__(self) -> None:
        self._online_users: dict[str, set[tuple[str, str]]] = {}

    def register_online(
        self, instance_id: str, platform: str, user_id: str
    ) -> None:
        """Register a user as online for an instance."""
        if instance_id not in self._online_users:
            self._online_users[instance_id] = set()
        self._online_users[instance_id].add((platform, user_id))

    def unregister_online(
        self, instance_id: str, platform: str, user_id: str
    ) -> None:
        """Unregister a user from online status."""
        if instance_id in self._online_users:
            self._online_users[instance_id].discard((platform, user_id))

    def get_online_users(
        self, instance_id: str
    ) -> list[tuple[str, str]]:
        """Get list of online users for an instance."""
        return list(self._online_users.get(instance_id, []))

    def format_online_status(self, instance_id: str, exclude_user: tuple[str, str] | None = None) -> str:
        """Format online users status message."""
        users = self.get_online_users(instance_id)

        if exclude_user:
            users = [u for u in users if u != exclude_user]

        if not users:
            return ""

        user_names = [f"@{user_id}" for _, user_id in users]
        return f"📡 在线用户: {', '.join(user_names)}"

    async def route(
        self,
        event: dict[str, Any],
        adapters: list["BaseAdapter"],
    ) -> None:
        """Route an OpenCode event to all relevant users."""
        instance_id = event.get("instance_id")
        if not instance_id:
            logger.warning("event_missing_instance_id", event=event)
            return

        online_users = self.get_online_users(instance_id)

        for platform, user_id in online_users:
            for adapter in adapters:
                if adapter.platform == platform:
                    try:
                        await adapter.send_event(user_id, event)
                    except Exception as e:
                        logger.error(
                            "send_event_failed",
                            platform=platform,
                            user_id=user_id,
                            error=str(e),
                        )

    async def broadcast(
        self,
        instance_id: str,
        message: str,
        adapters: list["BaseAdapter"],
        exclude: tuple[str, str] | None = None,
    ) -> None:
        """Broadcast a message to all online users of an instance."""
        online_users = self.get_online_users(instance_id)

        for platform, user_id in online_users:
            if exclude and (platform, user_id) == exclude:
                continue

            for adapter in adapters:
                if adapter.platform == platform:
                    try:
                        await adapter.send_text(user_id, message)
                    except Exception as e:
                        logger.error(
                            "broadcast_failed",
                            platform=platform,
                            user_id=user_id,
                            error=str(e),
                        )
