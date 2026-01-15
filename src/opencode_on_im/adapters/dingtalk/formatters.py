"""DingTalk message formatting utilities.

Provides:
- ActionCard templates for rich messages
- Markdown formatting for DingTalk
- Event formatting
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ActionButton:
    """An action button in a DingTalk ActionCard."""

    title: str
    action_url: str


@dataclass
class ActionCard:
    """DingTalk ActionCard message format.

    Reference: https://open.dingtalk.com/document/orgapp/message-types-and-data-format
    """

    title: str
    markdown: str
    btn_orientation: str = "0"  # 0: vertical, 1: horizontal
    buttons: list[ActionButton] = field(default_factory=list)
    single_title: str | None = None  # For single-button cards
    single_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to DingTalk API format."""
        if self.single_title and self.single_url:
            # Single-button card (整体跳转)
            return {
                "msgtype": "actionCard",
                "actionCard": {
                    "title": self.title,
                    "text": self.markdown,
                    "singleTitle": self.single_title,
                    "singleURL": self.single_url,
                },
            }
        else:
            # Multi-button card (独立跳转)
            return {
                "msgtype": "actionCard",
                "actionCard": {
                    "title": self.title,
                    "text": self.markdown,
                    "btnOrientation": self.btn_orientation,
                    "btns": [
                        {"title": btn.title, "actionURL": btn.action_url} for btn in self.buttons
                    ],
                },
            }


@dataclass
class MarkdownMessage:
    """DingTalk Markdown message format."""

    title: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to DingTalk API format."""
        return {
            "msgtype": "markdown",
            "markdown": {
                "title": self.title,
                "text": self.text,
            },
        }


@dataclass
class TextMessage:
    """DingTalk plain text message."""

    content: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to DingTalk API format."""
        return {
            "msgtype": "text",
            "text": {
                "content": self.content,
            },
        }


@dataclass
class LinkMessage:
    """DingTalk link message with preview."""

    title: str
    text: str
    message_url: str
    pic_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to DingTalk API format."""
        result = {
            "msgtype": "link",
            "link": {
                "title": self.title,
                "text": self.text,
                "messageUrl": self.message_url,
            },
        }
        if self.pic_url:
            result["link"]["picUrl"] = self.pic_url
        return result


def escape_markdown(text: str) -> str:
    """Escape special characters for DingTalk Markdown.

    DingTalk's Markdown is less strict than Telegram's.
    Only escape characters that cause issues.
    """
    # DingTalk markdown is relatively simple and doesn't need much escaping
    # Just ensure no accidental formatting
    text = text.replace("\\", "\\\\")
    return text


def format_code_block(code: str, language: str = "") -> str:  # noqa: ARG001
    """Format code block for DingTalk Markdown (no syntax highlighting support)."""
    return f"```\n{code}\n```"


def format_inline_code(text: str) -> str:
    """Format inline code."""
    return f"`{text}`"


def format_bold(text: str) -> str:
    """Format bold text."""
    return f"**{text}**"


def format_heading(text: str, level: int = 1) -> str:
    """Format heading (h1-h6)."""
    level = max(1, min(6, level))
    return f"{'#' * level} {text}"


def format_link(text: str, url: str) -> str:
    """Format a link."""
    return f"[{text}]({url})"


def format_quote(text: str) -> str:
    """Format a quote block."""
    lines = text.split("\n")
    return "\n".join(f"> {line}" for line in lines)


def format_list(items: list[str], ordered: bool = False) -> str:
    """Format a list."""
    if ordered:
        return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))
    return "\n".join(f"- {item}" for item in items)


# Pre-built card templates


def create_status_card(
    instance_name: str,
    status: str,
    session_count: int = 0,
    web_url: str | None = None,
) -> ActionCard:
    """Create a status card for an OpenCode instance."""
    status_emoji = {
        "idle": "💤",
        "busy": "⏳",
        "error": "❌",
        "connected": "✅",
        "disconnected": "🔌",
    }.get(status, "ℹ️")

    markdown = f"""### {status_emoji} {instance_name}

**状态**: {status}
**会话数**: {session_count}
"""

    buttons = []
    if web_url:
        buttons.append(ActionButton(title="打开 Web 终端", action_url=web_url))

    return ActionCard(
        title=f"实例状态: {instance_name}",
        markdown=markdown,
        buttons=buttons,
        btn_orientation="1",
    )


def create_bind_success_card(
    instance_name: str,
    instance_id: str,
    web_url: str | None = None,
) -> ActionCard:
    """Create a binding success card."""
    markdown = f"""### ✅ 绑定成功

**实例名称**: {instance_name}
**实例ID**: `{instance_id[:8]}...`

现在你可以:
- 直接发送消息与 AI 对话
- 发送图片让 AI 分析
- 使用 `/status` 查看状态
- 使用 `/web` 获取终端链接
"""

    buttons = []
    if web_url:
        buttons.append(ActionButton(title="打开 Web 终端", action_url=web_url))

    return ActionCard(
        title="绑定成功",
        markdown=markdown,
        buttons=buttons,
    )


def create_error_card(
    error_message: str,
    error_code: str | None = None,
    suggestion: str | None = None,
) -> ActionCard:
    """Create an error notification card."""
    markdown = f"""### ❌ 错误

**错误信息**: {error_message}
"""
    if error_code:
        markdown += f"**错误码**: `{error_code}`\n"
    if suggestion:
        markdown += f"\n**建议**: {suggestion}\n"

    return ActionCard(
        title="错误",
        markdown=markdown,
    )


def create_code_output_card(
    code: str,
    language: str = "",
    title: str = "代码输出",
) -> ActionCard:
    """Create a card for code output."""
    # Truncate if too long (DingTalk has limits)
    max_code_length = 2000
    truncated = len(code) > max_code_length
    display_code = code[:max_code_length] if truncated else code

    markdown = f"""### 📝 {title}

{format_code_block(display_code, language)}
"""
    if truncated:
        markdown += f"\n⚠️ *内容已截断 (原始长度: {len(code)} 字符)*\n"

    return ActionCard(
        title=title,
        markdown=markdown,
    )


def create_task_progress_card(
    task_name: str,
    progress: str,
    details: str | None = None,
) -> ActionCard:
    """Create a task progress card."""
    markdown = f"""### ⏳ {task_name}

**进度**: {progress}
"""
    if details:
        markdown += f"\n{details}\n"

    return ActionCard(
        title=f"任务: {task_name}",
        markdown=markdown,
    )


def format_event(event: dict[str, Any]) -> MarkdownMessage | ActionCard | TextMessage:
    """Format an OpenCode event for DingTalk.

    Args:
        event: OpenCode event dictionary

    Returns:
        Formatted message object
    """
    event_type = event.get("type", "unknown")

    if event_type == "message.part.updated":
        content = event.get("content", "")
        if len(content) > 100:
            return create_code_output_card(content, title="AI 输出")
        return TextMessage(content=content)

    if event_type == "message.created":
        role = event.get("role", "assistant")
        if role == "assistant":
            return MarkdownMessage(title="AI 响应", text="### 🤖 AI 开始响应")
        return TextMessage(content=f"消息: {role}")

    if event_type == "message.completed":
        return MarkdownMessage(title="完成", text="### ✅ 响应完成")

    if event_type == "session.status":
        status = event.get("status", "unknown")
        return MarkdownMessage(
            title="状态变更",
            text=f"### 状态: {status}",
        )

    if event_type == "error":
        error = event.get("message", "Unknown error")
        return create_error_card(error)

    if event_type == "tool.start":
        tool_name = event.get("tool", "unknown")
        return MarkdownMessage(
            title="工具执行",
            text=f"### 🔧 执行工具: `{tool_name}`",
        )

    if event_type == "tool.end":
        tool_name = event.get("tool", "unknown")
        success = event.get("success", True)
        emoji = "✅" if success else "❌"
        return MarkdownMessage(
            title="工具完成",
            text=f"### {emoji} 工具完成: `{tool_name}`",
        )

    # Default
    return TextMessage(content=f"事件: {event_type}")
