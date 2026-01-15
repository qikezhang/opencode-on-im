"""Tests for Telegram formatters."""

import pytest

from opencode_on_im.adapters.telegram.formatters import (
    TELEGRAM_MESSAGE_LIMIT,
    escape_markdown_v2,
    escape_markdown_v2_code,
    extract_code_blocks,
    format_bold,
    format_code_block,
    format_inline_code,
    format_italic,
    split_message,
)


class TestEscapeMarkdownV2:
    """Tests for MarkdownV2 escaping."""

    def test_escape_special_chars(self):
        """Test that all special characters are escaped."""
        text = "Hello_World*Bold[link](url)~strike`code`>quote#heading"
        escaped = escape_markdown_v2(text)

        assert "\\_" in escaped
        assert "\\*" in escaped
        assert "\\[" in escaped
        assert "\\]" in escaped
        assert "\\(" in escaped
        assert "\\)" in escaped
        assert "\\~" in escaped
        assert "\\`" in escaped
        assert "\\>" in escaped
        assert "\\#" in escaped

    def test_escape_empty_string(self):
        """Test escaping empty string."""
        assert escape_markdown_v2("") == ""

    def test_escape_plain_text(self):
        """Test that plain text without special chars is unchanged."""
        text = "Hello World 123"
        assert escape_markdown_v2(text) == text

    def test_escape_code_block_special(self):
        """Test code block escaping (only backticks and backslash)."""
        text = "console.log(`hello`)"
        escaped = escape_markdown_v2_code(text)

        assert "\\`" in escaped
        assert "_" not in escaped.replace("\\_", "")  # No double escape


class TestFormatting:
    """Tests for formatting functions."""

    def test_format_code_block_with_language(self):
        """Test code block with language."""
        result = format_code_block("print('hello')", "python")
        assert result.startswith("```python\n")
        assert result.endswith("\n```")

    def test_format_code_block_without_language(self):
        """Test code block without language."""
        result = format_code_block("some code")
        assert result.startswith("```\n")
        assert result.endswith("\n```")

    def test_format_inline_code(self):
        """Test inline code formatting."""
        result = format_inline_code("variable")
        assert result == "`variable`"

    def test_format_bold(self):
        """Test bold formatting."""
        result = format_bold("important")
        assert result == "*important*"

    def test_format_italic(self):
        """Test italic formatting."""
        result = format_italic("emphasis")
        assert result == "_emphasis_"

    def test_format_bold_with_special_chars(self):
        """Test bold with special characters escaped."""
        result = format_bold("hello_world")
        assert result == "*hello\\_world*"


class TestSplitMessage:
    """Tests for message splitting."""

    def test_short_message_no_split(self):
        """Test that short messages are not split."""
        text = "Short message"
        result = split_message(text)
        assert len(result) == 1
        assert result[0] == text

    def test_long_message_splits(self):
        """Test that long messages are split."""
        text = "a" * 5000  # Exceeds 4096 limit
        result = split_message(text)
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= TELEGRAM_MESSAGE_LIMIT

    def test_split_at_newline(self):
        """Test that split prefers newline boundaries."""
        # Create text with newlines
        text = ("Line " * 100 + "\n") * 50  # Multiple lines
        result = split_message(text)

        # Check that all chunks are within limit
        for chunk in result:
            assert len(chunk) <= TELEGRAM_MESSAGE_LIMIT

    def test_split_at_space(self):
        """Test that split prefers space boundaries when no newlines."""
        text = "word " * 1000  # Many words, no newlines
        result = split_message(text)

        # All chunks should be within limit
        for chunk in result:
            assert len(chunk) <= TELEGRAM_MESSAGE_LIMIT

    def test_exact_limit(self):
        """Test message exactly at limit."""
        text = "a" * TELEGRAM_MESSAGE_LIMIT
        result = split_message(text)
        assert len(result) == 1


class TestExtractCodeBlocks:
    """Tests for code block extraction."""

    def test_single_code_block(self):
        """Test extracting a single code block."""
        text = "Before\n```python\nprint('hello')\n```\nAfter"
        parts = extract_code_blocks(text)

        assert len(parts) == 3
        assert parts[0]["type"] == "text"
        assert parts[1]["type"] == "code"
        assert parts[1]["language"] == "python"
        assert parts[1]["content"].strip() == "print('hello')"
        assert parts[2]["type"] == "text"

    def test_multiple_code_blocks(self):
        """Test extracting multiple code blocks."""
        text = "```js\nconst x = 1;\n```\nText\n```python\ny = 2\n```"
        parts = extract_code_blocks(text)

        code_parts = [p for p in parts if p["type"] == "code"]
        assert len(code_parts) == 2
        assert code_parts[0]["language"] == "js"
        assert code_parts[1]["language"] == "python"

    def test_code_block_no_language(self):
        """Test code block without language specifier."""
        text = "```\ncode here\n```"
        parts = extract_code_blocks(text)

        assert len(parts) == 1
        assert parts[0]["type"] == "code"
        assert parts[0]["language"] == ""

    def test_no_code_blocks(self):
        """Test text without code blocks."""
        text = "Just plain text"
        parts = extract_code_blocks(text)

        assert len(parts) == 1
        assert parts[0]["type"] == "text"
        assert parts[0]["content"] == text

    def test_empty_text(self):
        """Test empty text."""
        parts = extract_code_blocks("")

        assert len(parts) == 1
        assert parts[0]["content"] == ""
