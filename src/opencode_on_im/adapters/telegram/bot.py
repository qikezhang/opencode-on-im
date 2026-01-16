"""Telegram Bot adapter using aiogram 3.x.

Provides:
- Message sending with MarkdownV2 formatting
- Image sending with size limits and compression
- Card/button support
- Event formatting
"""

from io import BytesIO
from typing import Any

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile
from PIL import Image
from PIL.Image import Image as PILImage

from opencode_on_im.adapters.base import BaseAdapter
from opencode_on_im.adapters.telegram.handlers import setup_handlers
from opencode_on_im.core.config import Settings
from opencode_on_im.core.instance import InstanceRegistry
from opencode_on_im.core.notification import NotificationRouter
from opencode_on_im.core.session import SessionManager
from opencode_on_im.opencode.client import OpenCodeClient

logger = structlog.get_logger()

# Telegram limits
TELEGRAM_MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB
TELEGRAM_MAX_CAPTION_LENGTH = 1024
TELEGRAM_PHOTO_MAX_DIMENSION = 4096  # Max width/height


class TelegramAdapter(BaseAdapter):
    """Telegram IM adapter using aiogram 3.x."""

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
        self.opencode_client = OpenCodeClient(settings)

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
        await self.opencode_client.close()

    async def send_text(
        self,
        user_id: str,
        text: str,
        parse_mode: str | None = None,
    ) -> None:
        """Send text message with optional parse mode."""
        pm = (
            ParseMode.MARKDOWN_V2
            if parse_mode is None
            else getattr(ParseMode, parse_mode.upper(), None)
        )
        await self.bot.send_message(chat_id=int(user_id), text=text, parse_mode=pm)

    async def send_image(
        self,
        user_id: str,
        image: bytes,
        caption: str | None = None,
    ) -> None:
        """Send image with automatic compression if needed.

        Handles:
        - Size limits (max 10MB)
        - Dimension limits (max 4096px)
        - Caption length limits (max 1024 chars)
        - Automatic JPEG compression for oversized images
        """
        # Process image if needed
        processed_image = await self._process_image(image)

        # Truncate caption if too long
        if caption and len(caption) > TELEGRAM_MAX_CAPTION_LENGTH:
            caption = caption[: TELEGRAM_MAX_CAPTION_LENGTH - 3] + "..."
            logger.debug("caption_truncated", original_len=len(caption))

        photo = BufferedInputFile(processed_image, filename="output.png")
        await self.bot.send_photo(chat_id=int(user_id), photo=photo, caption=caption)

    async def _process_image(self, image_bytes: bytes) -> bytes:
        """Process image to fit Telegram limits.

        - Resize if dimensions exceed 4096px
        - Compress to JPEG if size exceeds 10MB
        """
        # Check if processing is needed
        if len(image_bytes) <= TELEGRAM_MAX_PHOTO_SIZE:
            # Check dimensions
            try:
                check_img = Image.open(BytesIO(image_bytes))
                if max(check_img.size) <= TELEGRAM_PHOTO_MAX_DIMENSION:
                    # Image is fine as-is
                    return image_bytes
            except Exception:
                # Can't read image, return as-is
                return image_bytes

        # Process image
        try:
            img: PILImage = Image.open(BytesIO(image_bytes))  # type: ignore[assignment]

            # Resize if needed
            if max(img.size) > TELEGRAM_PHOTO_MAX_DIMENSION:
                ratio = TELEGRAM_PHOTO_MAX_DIMENSION / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)  # type: ignore[assignment]
                logger.debug("image_resized", original=img.size, new=new_size)

            # Try PNG first
            buffer = BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            if buffer.tell() <= TELEGRAM_MAX_PHOTO_SIZE:
                return buffer.getvalue()

            # Compress to JPEG with decreasing quality
            for quality in [95, 85, 75, 60, 45]:
                buffer = BytesIO()
                # Convert to RGB for JPEG (drop alpha)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")  # type: ignore[assignment]
                img.save(buffer, format="JPEG", quality=quality, optimize=True)
                if buffer.tell() <= TELEGRAM_MAX_PHOTO_SIZE:
                    logger.debug("image_compressed", quality=quality, size=buffer.tell())
                    return buffer.getvalue()

            # Last resort: aggressive resize + low quality
            while max(img.size) > 800:
                new_size = (img.size[0] // 2, img.size[1] // 2)
                img = img.resize(new_size, Image.Resampling.LANCZOS)  # type: ignore[assignment]

            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=40, optimize=True)
            logger.warning("image_heavily_compressed", size=buffer.tell())
            return buffer.getvalue()

        except Exception as e:
            logger.error("image_processing_failed", error=str(e))
            # Return original if processing fails
            return image_bytes

    async def send_card(
        self,
        user_id: str,
        title: str,
        content: str,
        buttons: list[dict[str, Any]],
    ) -> None:
        """Send message with inline keyboard buttons."""
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        from opencode_on_im.adapters.telegram.formatters import escape_markdown_v2

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=btn["text"], url=btn.get("url"), callback_data=btn.get("callback")
                    )
                ]
                for btn in buttons
            ]
        )

        # Format with MarkdownV2
        escaped_title = escape_markdown_v2(title)
        escaped_content = escape_markdown_v2(content)
        text = f"*{escaped_title}*\n\n{escaped_content}"

        await self.bot.send_message(chat_id=int(user_id), text=text, reply_markup=keyboard)

    async def send_event(self, user_id: str, event: dict[str, Any]) -> None:
        """Send formatted OpenCode event to user."""
        from opencode_on_im.adapters.telegram.formatters import format_event

        formatted = await format_event(event, self.settings)

        if formatted.image:
            await self.send_image(user_id, formatted.image, formatted.text)
        else:
            await self.send_text(user_id, formatted.text)

    async def send_document(
        self,
        user_id: str,
        document: bytes,
        filename: str,
        caption: str | None = None,
    ) -> None:
        """Send file as document (for large files or non-image content)."""
        doc = BufferedInputFile(document, filename=filename)

        if caption and len(caption) > TELEGRAM_MAX_CAPTION_LENGTH:
            caption = caption[: TELEGRAM_MAX_CAPTION_LENGTH - 3] + "..."

        await self.bot.send_document(chat_id=int(user_id), document=doc, caption=caption)
