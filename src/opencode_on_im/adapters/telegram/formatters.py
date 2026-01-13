from dataclasses import dataclass
from typing import Any

from opencode_on_im.core.config import Settings
from opencode_on_im.renderers.image import render_code_to_image


@dataclass
class FormattedMessage:
    text: str
    image: bytes | None = None


async def format_event(event: dict[str, Any], settings: Settings) -> FormattedMessage:
    event_type = event.get("type", "unknown")

    if event_type == "message.part.updated":
        content = event.get("content", "")

        lines = content.split("\n")
        if len(lines) > settings.message_image_threshold:
            image = await render_code_to_image(content)
            return FormattedMessage(text="代码输出 \\(见图片\\)", image=image)

        escaped = escape_markdown(content)
        return FormattedMessage(text=escaped)

    if event_type == "session.status":
        status = event.get("status", "unknown")
        return FormattedMessage(text=f"状态: `{status}`")

    if event_type == "error":
        error = event.get("message", "Unknown error")
        return FormattedMessage(text=f"❌ 错误: {escape_markdown(error)}")

    return FormattedMessage(text=f"事件: `{event_type}`")


def escape_markdown(text: str) -> str:
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text
