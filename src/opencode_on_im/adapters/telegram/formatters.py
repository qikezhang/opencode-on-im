"""Telegram message formatting utilities.

Handles:
- MarkdownV2 escaping and formatting
- Long message splitting (Telegram 4096 char limit)
- Code block detection and rendering
"""

import re
from dataclasses import dataclass, field
from typing import Any

from opencode_on_im.core.config import Settings
from opencode_on_im.renderers.image import ContentRenderer, render_code_to_image

# Telegram message limits
TELEGRAM_MESSAGE_LIMIT = 4096
TELEGRAM_CAPTION_LIMIT = 1024

# Characters that must be escaped in MarkdownV2
MARKDOWN_V2_SPECIAL_CHARS = r"_*[]()~`>#+-=|{}.!"


@dataclass
class FormattedMessage:
    """A formatted message ready for sending."""

    text: str
    image: bytes | None = None
    parse_mode: str = "MarkdownV2"


@dataclass
class SplitMessages:
    """Multiple messages split from long content."""

    messages: list[FormattedMessage] = field(default_factory=list)

    def add_text(self, text: str, parse_mode: str = "MarkdownV2") -> None:
        """Add a text message."""
        self.messages.append(FormattedMessage(text=text, parse_mode=parse_mode))

    def add_image(self, image: bytes, caption: str = "") -> None:
        """Add an image message."""
        self.messages.append(FormattedMessage(text=caption, image=image))


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2.

    Reference: https://core.telegram.org/bots/api#markdownv2-style
    """
    # Escape all special characters
    result = ""
    for char in text:
        if char in MARKDOWN_V2_SPECIAL_CHARS:
            result += f"\\{char}"
        else:
            result += char
    return result


def escape_markdown_v2_code(text: str) -> str:
    """Escape for inline code or code blocks (only ` and \\ need escaping)."""
    return text.replace("\\", "\\\\").replace("`", "\\`")


def format_code_block(code: str, language: str = "") -> str:
    """Format text as a MarkdownV2 code block."""
    escaped_code = escape_markdown_v2_code(code)
    if language:
        return f"```{language}\n{escaped_code}\n```"
    return f"```\n{escaped_code}\n```"


def format_inline_code(text: str) -> str:
    """Format text as inline code."""
    return f"`{escape_markdown_v2_code(text)}`"


def format_bold(text: str) -> str:
    """Format text as bold."""
    return f"*{escape_markdown_v2(text)}*"


def format_italic(text: str) -> str:
    """Format text as italic."""
    return f"_{escape_markdown_v2(text)}_"


def split_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    """Split a long message into chunks that fit Telegram's limit.

    Tries to split at natural boundaries (newlines, spaces) when possible.
    Handles code blocks specially to avoid breaking them.
    """
    if len(text) <= limit:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break

        # Find a good split point
        split_point = _find_split_point(remaining, limit)
        chunks.append(remaining[:split_point].rstrip())
        remaining = remaining[split_point:].lstrip()

    return chunks


def _find_split_point(text: str, limit: int) -> int:
    """Find the best point to split text."""
    # Try to split at double newline (paragraph)
    last_para = text.rfind("\n\n", 0, limit)
    if last_para > limit // 2:
        return last_para + 2

    # Try to split at single newline
    last_newline = text.rfind("\n", 0, limit)
    if last_newline > limit // 2:
        return last_newline + 1

    # Try to split at space
    last_space = text.rfind(" ", 0, limit)
    if last_space > limit // 2:
        return last_space + 1

    # Hard split at limit
    return limit


def extract_code_blocks(text: str) -> list[dict[str, Any]]:
    """Extract code blocks from markdown text.

    Returns list of dicts with 'type' ('text' or 'code'), 'content', and 'language'.
    """
    pattern = r"```(\w*)\n?(.*?)```"
    parts = []
    last_end = 0

    for match in re.finditer(pattern, text, re.DOTALL):
        # Add text before code block
        if match.start() > last_end:
            text_part = text[last_end : match.start()]
            if text_part.strip():
                parts.append({"type": "text", "content": text_part})

        # Add code block
        parts.append(
            {
                "type": "code",
                "content": match.group(2),
                "language": match.group(1) or "",
            }
        )
        last_end = match.end()

    # Add remaining text
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining.strip():
            parts.append({"type": "text", "content": remaining})

    # If no code blocks found, return whole text
    if not parts:
        parts.append({"type": "text", "content": text})

    return parts


async def format_event(event: dict[str, Any], settings: Settings) -> FormattedMessage:
    """Format an OpenCode event for Telegram.

    Handles different event types and applies appropriate formatting.
    """
    event_type = event.get("type", "unknown")

    if event_type == "message.part.updated":
        return await _format_message_content(event, settings)

    if event_type == "message.created":
        role = event.get("role", "assistant")
        if role == "assistant":
            return FormattedMessage(text="🤖 *AI 开始响应*", parse_mode="MarkdownV2")
        return FormattedMessage(text=f"📝 {escape_markdown_v2(role)}", parse_mode="MarkdownV2")

    if event_type == "message.completed":
        return FormattedMessage(text="✅ *响应完成*", parse_mode="MarkdownV2")

    if event_type == "session.status":
        status = event.get("status", "unknown")
        status_emoji = {
            "idle": "💤",
            "busy": "⏳",
            "error": "❌",
            "completed": "✅",
        }.get(status, "ℹ️")
        return FormattedMessage(
            text=f"{status_emoji} 状态: `{escape_markdown_v2_code(status)}`",
            parse_mode="MarkdownV2",
        )

    if event_type == "error":
        error = event.get("message", "Unknown error")
        return FormattedMessage(
            text=f"❌ *错误*: {escape_markdown_v2(error)}",
            parse_mode="MarkdownV2",
        )

    if event_type == "tool.start":
        tool_name = event.get("tool", "unknown")
        return FormattedMessage(
            text=f"🔧 执行工具: `{escape_markdown_v2_code(tool_name)}`",
            parse_mode="MarkdownV2",
        )

    if event_type == "tool.end":
        tool_name = event.get("tool", "unknown")
        success = event.get("success", True)
        emoji = "✅" if success else "❌"
        return FormattedMessage(
            text=f"{emoji} 工具完成: `{escape_markdown_v2_code(tool_name)}`",
            parse_mode="MarkdownV2",
        )

    # Default: show event type
    return FormattedMessage(
        text=f"ℹ️ 事件: `{escape_markdown_v2_code(event_type)}`",
        parse_mode="MarkdownV2",
    )


async def _format_message_content(
    event: dict[str, Any], settings: Settings
) -> FormattedMessage:
    """Format message content, handling long content and code blocks."""
    content = event.get("content", "")

    if not content:
        return FormattedMessage(text="", parse_mode="MarkdownV2")

    # Use ContentRenderer to check if we should render as image
    renderer = ContentRenderer(settings)

    # Check for code blocks
    parts = extract_code_blocks(content)
    has_code = any(p["type"] == "code" for p in parts)

    # If content is very long or has long code blocks, render as image
    if renderer.should_render_as_image(content):
        if has_code:
            # Find the main code block
            code_parts = [p for p in parts if p["type"] == "code"]
            if code_parts:
                main_code = code_parts[0]
                image = await render_code_to_image(
                    main_code["content"], language=main_code.get("language")
                )
                return FormattedMessage(
                    text="📝 *代码输出* \\(见图片\\)",
                    image=image,
                    parse_mode="MarkdownV2",
                )

        # Render as text image
        image = await renderer.render_text(content)
        return FormattedMessage(
            text="📄 *输出* \\(见图片\\)",
            image=image,
            parse_mode="MarkdownV2",
        )

    # Format as text with proper escaping
    formatted_parts = []
    for part in parts:
        if part["type"] == "code":
            formatted_parts.append(format_code_block(part["content"], part.get("language", "")))
        else:
            formatted_parts.append(escape_markdown_v2(part["content"]))

    formatted_text = "".join(formatted_parts)

    # Split if still too long
    if len(formatted_text) > TELEGRAM_MESSAGE_LIMIT:
        # For very long text without code, just escape and truncate
        truncated = formatted_text[: TELEGRAM_MESSAGE_LIMIT - 20] + "\n\\.\\.\\. \\(已截断\\)"
        return FormattedMessage(text=truncated, parse_mode="MarkdownV2")

    return FormattedMessage(text=formatted_text, parse_mode="MarkdownV2")


async def format_for_split_send(
    content: str, settings: Settings
) -> SplitMessages:
    """Format content for sending as multiple messages if needed.

    Use this for very long content that needs to be split.
    """
    result = SplitMessages()
    renderer = ContentRenderer(settings)

    # If short enough, just format and return
    if not renderer.should_render_as_image(content):
        escaped = escape_markdown_v2(content)
        chunks = split_message(escaped)
        for chunk in chunks:
            result.add_text(chunk)
        return result

    # For long content, check for code blocks
    parts = extract_code_blocks(content)

    for part in parts:
        if part["type"] == "code":
            code = part["content"]
            language = part.get("language", "")

            # Render code as image
            image = await render_code_to_image(code, language=language)
            result.add_image(image, f"```{language}```" if language else "")

        else:
            text = part["content"]
            if len(text) > TELEGRAM_MESSAGE_LIMIT:
                # Split long text
                escaped = escape_markdown_v2(text)
                chunks = split_message(escaped)
                for chunk in chunks:
                    result.add_text(chunk)
            else:
                result.add_text(escape_markdown_v2(text))

    return result
