"""Tests for DingTalk formatters."""

import pytest

from opencode_on_im.adapters.dingtalk.formatters import (
    ActionButton,
    ActionCard,
    LinkMessage,
    MarkdownMessage,
    TextMessage,
    create_bind_success_card,
    create_code_output_card,
    create_error_card,
    create_status_card,
    create_task_progress_card,
    escape_markdown,
    format_bold,
    format_code_block,
    format_event,
    format_heading,
    format_inline_code,
    format_link,
    format_list,
    format_quote,
)


class TestActionCard:
    def test_single_button_card(self):
        card = ActionCard(
            title="Test",
            markdown="# Hello",
            single_title="Click",
            single_url="https://example.com",
        )
        result = card.to_dict()
        assert result["msgtype"] == "actionCard"
        assert result["actionCard"]["singleTitle"] == "Click"
        assert result["actionCard"]["singleURL"] == "https://example.com"

    def test_multi_button_card(self):
        card = ActionCard(
            title="Test",
            markdown="# Hello",
            buttons=[
                ActionButton(title="Button 1", action_url="https://a.com"),
                ActionButton(title="Button 2", action_url="https://b.com"),
            ],
            btn_orientation="1",
        )
        result = card.to_dict()
        assert result["msgtype"] == "actionCard"
        assert len(result["actionCard"]["btns"]) == 2
        assert result["actionCard"]["btnOrientation"] == "1"


class TestMessageTypes:
    def test_markdown_message(self):
        msg = MarkdownMessage(title="Test", text="# Hello")
        result = msg.to_dict()
        assert result["msgtype"] == "markdown"
        assert result["markdown"]["title"] == "Test"
        assert result["markdown"]["text"] == "# Hello"

    def test_text_message(self):
        msg = TextMessage(content="Hello world")
        result = msg.to_dict()
        assert result["msgtype"] == "text"
        assert result["text"]["content"] == "Hello world"

    def test_link_message_without_pic(self):
        msg = LinkMessage(
            title="Link",
            text="Description",
            message_url="https://example.com",
        )
        result = msg.to_dict()
        assert result["msgtype"] == "link"
        assert "picUrl" not in result["link"]

    def test_link_message_with_pic(self):
        msg = LinkMessage(
            title="Link",
            text="Description",
            message_url="https://example.com",
            pic_url="https://example.com/pic.png",
        )
        result = msg.to_dict()
        assert result["link"]["picUrl"] == "https://example.com/pic.png"


class TestFormatting:
    def test_escape_markdown(self):
        assert escape_markdown("hello\\world") == "hello\\\\world"
        assert escape_markdown("normal text") == "normal text"

    def test_format_code_block(self):
        result = format_code_block("print('hello')", "python")
        assert "```" in result
        assert "print('hello')" in result

    def test_format_inline_code(self):
        assert format_inline_code("code") == "`code`"

    def test_format_bold(self):
        assert format_bold("text") == "**text**"

    def test_format_heading(self):
        assert format_heading("Title", 1) == "# Title"
        assert format_heading("Title", 2) == "## Title"
        assert format_heading("Title", 7) == "###### Title"  # clamped to 6
        assert format_heading("Title", 0) == "# Title"  # clamped to 1

    def test_format_link(self):
        assert format_link("text", "https://example.com") == "[text](https://example.com)"

    def test_format_quote(self):
        result = format_quote("line1\nline2")
        assert result == "> line1\n> line2"

    def test_format_list_unordered(self):
        result = format_list(["a", "b", "c"])
        assert result == "- a\n- b\n- c"

    def test_format_list_ordered(self):
        result = format_list(["a", "b", "c"], ordered=True)
        assert result == "1. a\n2. b\n3. c"


class TestCardTemplates:
    def test_create_status_card(self):
        card = create_status_card(
            instance_name="test-instance",
            status="connected",
            session_count=5,
            web_url="https://example.com",
        )
        assert isinstance(card, ActionCard)
        assert "test-instance" in card.markdown
        assert "✅" in card.markdown
        assert len(card.buttons) == 1

    def test_create_status_card_no_web(self):
        card = create_status_card(
            instance_name="test",
            status="idle",
            session_count=0,
        )
        assert len(card.buttons) == 0
        assert "💤" in card.markdown

    def test_create_bind_success_card(self):
        card = create_bind_success_card(
            instance_name="my-instance",
            instance_id="12345678-1234-1234-1234-123456789012",
            web_url="https://example.com",
        )
        assert "绑定成功" in card.markdown
        assert "my-instance" in card.markdown
        assert len(card.buttons) == 1

    def test_create_error_card(self):
        card = create_error_card(
            error_message="Something went wrong",
            error_code="E001",
            suggestion="Try again",
        )
        assert "Something went wrong" in card.markdown
        assert "E001" in card.markdown
        assert "Try again" in card.markdown

    def test_create_error_card_minimal(self):
        card = create_error_card(error_message="Error")
        assert "Error" in card.markdown

    def test_create_code_output_card(self):
        card = create_code_output_card(
            code="print('hello')",
            language="python",
            title="Output",
        )
        assert "print('hello')" in card.markdown
        assert "Output" in card.title

    def test_create_code_output_card_truncated(self):
        long_code = "x" * 3000
        card = create_code_output_card(code=long_code)
        assert "截断" in card.markdown
        assert "3000" in card.markdown

    def test_create_task_progress_card(self):
        card = create_task_progress_card(
            task_name="Build",
            progress="50%",
            details="Building modules...",
        )
        assert "Build" in card.markdown
        assert "50%" in card.markdown
        assert "Building modules" in card.markdown


class TestFormatEvent:
    def test_message_part_updated_short(self):
        result = format_event({"type": "message.part.updated", "content": "Hello"})
        assert isinstance(result, TextMessage)
        assert result.content == "Hello"

    def test_message_part_updated_long(self):
        result = format_event({"type": "message.part.updated", "content": "x" * 200})
        assert isinstance(result, ActionCard)

    def test_message_created_assistant(self):
        result = format_event({"type": "message.created", "role": "assistant"})
        assert isinstance(result, MarkdownMessage)
        assert "AI" in result.text

    def test_message_created_other(self):
        result = format_event({"type": "message.created", "role": "user"})
        assert isinstance(result, TextMessage)

    def test_message_completed(self):
        result = format_event({"type": "message.completed"})
        assert isinstance(result, MarkdownMessage)
        assert "完成" in result.text

    def test_session_status(self):
        result = format_event({"type": "session.status", "status": "busy"})
        assert isinstance(result, MarkdownMessage)
        assert "busy" in result.text

    def test_error_event(self):
        result = format_event({"type": "error", "message": "Failed"})
        assert isinstance(result, ActionCard)
        assert "Failed" in result.markdown

    def test_tool_start(self):
        result = format_event({"type": "tool.start", "tool": "read_file"})
        assert isinstance(result, MarkdownMessage)
        assert "read_file" in result.text

    def test_tool_end_success(self):
        result = format_event({"type": "tool.end", "tool": "write_file", "success": True})
        assert isinstance(result, MarkdownMessage)
        assert "✅" in result.text

    def test_tool_end_failure(self):
        result = format_event({"type": "tool.end", "tool": "exec", "success": False})
        assert isinstance(result, MarkdownMessage)
        assert "❌" in result.text

    def test_unknown_event(self):
        result = format_event({"type": "custom.event"})
        assert isinstance(result, TextMessage)
        assert "custom.event" in result.content
