"""DingTalk Stream Mode adapter using dingtalk-stream SDK."""

from typing import Any
import asyncio
import base64
import json

import structlog

try:
    import dingtalk_stream
    from dingtalk_stream import ChatbotHandler, ChatbotMessage, AckMessage
    DINGTALK_AVAILABLE = True
except ImportError:
    DINGTALK_AVAILABLE = False
    dingtalk_stream = None
    ChatbotHandler = object

from opencode_on_im.adapters.base import BaseAdapter
from opencode_on_im.core.config import Settings
from opencode_on_im.core.instance import InstanceRegistry
from opencode_on_im.core.notification import NotificationRouter
from opencode_on_im.core.session import SessionManager

logger = structlog.get_logger()


class DingTalkAdapter(BaseAdapter):
    """DingTalk adapter using Stream mode (WebSocket).

    Stream mode advantages:
    - No public IP required
    - No webhook URL configuration needed
    - Real-time bidirectional communication
    """

    def __init__(
        self,
        settings: Settings,
        session_manager: SessionManager,
        instance_registry: InstanceRegistry,
        notification_router: NotificationRouter,
    ) -> None:
        super().__init__(
            settings, session_manager, instance_registry, notification_router
        )
        self._running = False
        self._client: Any = None
        self._task: asyncio.Task[None] | None = None
        self._handler: Any = None

    @property
    def platform(self) -> str:
        return "dingtalk"

    async def start(self) -> None:
        """Start the DingTalk Stream client."""
        if not DINGTALK_AVAILABLE:
            logger.error(
                "dingtalk_stream_not_installed",
                hint="pip install dingtalk-stream",
            )
            return

        if not self.settings.dingtalk.app_key or not self.settings.dingtalk.app_secret:
            logger.warning("dingtalk_credentials_missing")
            return

        logger.info("dingtalk_adapter_starting")

        # Initialize credentials
        credential = dingtalk_stream.Credential(
            client_id=self.settings.dingtalk.app_key,
            client_secret=self.settings.dingtalk.app_secret,
        )

        # Create stream client
        self._client = dingtalk_stream.DingTalkStreamClient(credential)

        # Create and register chatbot handler
        self._handler = self._create_handler()
        self._client.register_callback_handler(
            dingtalk_stream.ChatbotMessage.TOPIC,
            self._handler,
        )

        # Start in background task
        self._running = True
        self._task = asyncio.create_task(self._run_client())

        logger.info("dingtalk_adapter_started")

    def _create_handler(self) -> Any:
        """Create the chatbot message handler."""
        adapter = self

        class Handler(ChatbotHandler):  # type: ignore
            async def process(self, callback: Any) -> tuple[str, str]:
                try:
                    incoming = ChatbotMessage.from_dict(callback.data)
                    text = incoming.text.content.strip() if incoming.text else ""
                    sender_id = incoming.sender_staff_id or incoming.sender_id
                    sender_nick = incoming.sender_nick or "Unknown"

                    logger.info(
                        "dingtalk_message_received",
                        sender_id=sender_id,
                        sender_nick=sender_nick,
                        text_len=len(text),
                    )

                    # Handle QR code binding
                    if text.startswith("eyJ"):
                        await adapter._handle_qr_bind(sender_id, text, self, incoming)
                    else:
                        # Check if user has bound instances
                        instances = await adapter.session_manager.get_user_instances(
                            "dingtalk", sender_id
                        )
                        if not instances:
                            self.reply_text(
                                "请先扫描 OpenCode 实例二维码进行绑定。",
                                incoming,
                            )
                        else:
                            # TODO: Forward to OpenCode
                            self.reply_text(
                                f"收到消息 ({len(text)} 字符)，正在处理...",
                                incoming,
                            )

                    return AckMessage.STATUS_OK, "OK"

                except Exception as e:
                    logger.error("dingtalk_handler_error", error=str(e))
                    return AckMessage.STATUS_SYSTEM_EXCEPTION, str(e)

        return Handler()

    async def _handle_qr_bind(
        self,
        user_id: str,
        qr_data: str,
        handler: Any,
        incoming: Any,
    ) -> None:
        """Handle QR code binding."""
        try:
            data = json.loads(base64.urlsafe_b64decode(qr_data))
            instance_id = data.get("instance_id")
            connect_secret = data.get("connect_secret")

            if self.instance_registry.verify_connect_secret(instance_id, connect_secret):
                await self.session_manager.bind_user("dingtalk", user_id, instance_id)
                instance = self.instance_registry.get_instance(instance_id)
                self.notification_router.register_online(
                    instance_id, "dingtalk", user_id
                )

                handler.reply_markdown(
                    "绑定成功",
                    f"### ✅ 绑定成功\n\n"
                    f"**实例**: {instance.name if instance else instance_id}\n\n"
                    f"现在可以开始发送消息了！",
                    incoming,
                )
            else:
                handler.reply_text("二维码无效或已过期", incoming)

        except Exception as e:
            logger.error("dingtalk_qr_bind_error", error=str(e))
            handler.reply_text("绑定失败，请检查二维码", incoming)

    async def _run_client(self) -> None:
        """Run the DingTalk stream client."""
        try:
            await self._client.start()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("dingtalk_client_error", error=str(e))

    async def stop(self) -> None:
        """Stop the DingTalk adapter."""
        logger.info("dingtalk_adapter_stopping")
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._client = None
        self._handler = None
        logger.info("dingtalk_adapter_stopped")

    async def send_text(
        self,
        user_id: str,
        text: str,
        parse_mode: str | None = None,  # noqa: ARG002
    ) -> None:
        """Send text message to user.

        Note: DingTalk Stream mode doesn't support proactive messages easily.
        Messages are typically sent as replies to incoming messages.
        """
        logger.info("dingtalk_send_text", user_id=user_id, text_len=len(text))
        # TODO: Implement proactive messaging using DingTalk Open API

    async def send_image(
        self,
        user_id: str,
        image: bytes,
        caption: str | None = None,  # noqa: ARG002
    ) -> None:
        """Send image to user."""
        logger.info("dingtalk_send_image", user_id=user_id, image_size=len(image))
        # TODO: Upload image to DingTalk media API first

    async def send_card(
        self,
        user_id: str,
        title: str,
        content: str,  # noqa: ARG002
        buttons: list[dict[str, Any]],  # noqa: ARG002
    ) -> None:
        """Send card message to user."""
        logger.info("dingtalk_send_card", user_id=user_id, title=title)
        # TODO: Implement interactive card

    async def send_event(self, user_id: str, event: dict[str, Any]) -> None:
        """Send OpenCode event to user."""
        event_type = event.get("type", "unknown")
        logger.info("dingtalk_send_event", user_id=user_id, event_type=event_type)
        # Events are handled through the chatbot handler replies
