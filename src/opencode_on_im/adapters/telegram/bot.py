from typing import Any

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile

from opencode_on_im.adapters.base import BaseAdapter
from opencode_on_im.adapters.telegram.handlers import setup_handlers
from opencode_on_im.core.config import Settings
from opencode_on_im.core.instance import InstanceRegistry
from opencode_on_im.core.notification import NotificationRouter
from opencode_on_im.core.session import SessionManager

logger = structlog.get_logger()


class TelegramAdapter(BaseAdapter):

    def __init__(
        self,
        settings: Settings,
        session_manager: SessionManager,
        instance_registry: InstanceRegistry,
        notification_router: NotificationRouter,
    ) -> None:
        super().__init__(settings, session_manager, instance_registry, notification_router)

        assert settings.telegram.token is not None
        self.bot = Bot(
            token=settings.telegram.token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2),
        )
        self.dp = Dispatcher()
        setup_handlers(self.dp, self)

    @property
    def platform(self) -> str:
        return "telegram"

    async def start(self) -> None:
        logger.info("telegram_adapter_starting")
        await self.dp.start_polling(self.bot)

    async def stop(self) -> None:
        logger.info("telegram_adapter_stopping")
        await self.dp.stop_polling()
        await self.bot.session.close()

    async def send_text(
        self,
        user_id: str,
        text: str,
        parse_mode: str | None = None,
    ) -> None:
        pm = ParseMode.MARKDOWN_V2 if parse_mode is None else getattr(ParseMode, parse_mode.upper(), None)
        await self.bot.send_message(chat_id=int(user_id), text=text, parse_mode=pm)

    async def send_image(
        self,
        user_id: str,
        image: bytes,
        caption: str | None = None,
    ) -> None:
        photo = BufferedInputFile(image, filename="output.png")
        await self.bot.send_photo(chat_id=int(user_id), photo=photo, caption=caption)

    async def send_card(
        self,
        user_id: str,
        title: str,
        content: str,
        buttons: list[dict[str, Any]],
    ) -> None:
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=btn["text"], url=btn.get("url"), callback_data=btn.get("callback"))]
                for btn in buttons
            ]
        )

        text = f"**{title}**\n\n{content}"
        await self.bot.send_message(chat_id=int(user_id), text=text, reply_markup=keyboard)

    async def send_event(self, user_id: str, event: dict[str, Any]) -> None:
        from opencode_on_im.adapters.telegram.formatters import format_event

        formatted = await format_event(event, self.settings)

        if formatted.image:
            await self.send_image(user_id, formatted.image, formatted.text)
        else:
            await self.send_text(user_id, formatted.text)
