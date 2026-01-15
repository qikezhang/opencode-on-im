"""Tests for image rendering functions (using mock Settings to avoid import issues)."""

from unittest.mock import MagicMock

import pytest

# ============================================================================
# Test: render_code_to_image
# ============================================================================


class TestRenderCodeToImage:
    """Tests for code rendering with syntax highlighting."""

    @pytest.mark.asyncio
    async def test_render_python_code(self) -> None:
        """Render Python code with syntax highlighting."""
        from opencode_on_im.renderers.image import render_code_to_image

        code = 'def hello():\n    print("Hello")'
        result = await render_code_to_image(code, language="python")

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    @pytest.mark.asyncio
    async def test_render_auto_detect_language(self) -> None:
        """Auto-detect language when not specified."""
        from opencode_on_im.renderers.image import render_code_to_image

        code = "#!/usr/bin/env python\nprint('hi')"
        result = await render_code_to_image(code)

        assert isinstance(result, bytes)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    @pytest.mark.asyncio
    async def test_render_unknown_language_fallback(self) -> None:
        """Fall back to plain text for unknown language."""
        from opencode_on_im.renderers.image import render_code_to_image

        code = "plain text"
        result = await render_code_to_image(code, language="nonexistent_xyz")

        assert isinstance(result, bytes)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"


# ============================================================================
# Test: render_text_to_image
# ============================================================================


class TestRenderTextToImage:
    """Tests for plain text rendering."""

    @pytest.mark.asyncio
    async def test_render_simple_text(self) -> None:
        """Render simple text."""
        from opencode_on_im.renderers.image import render_text_to_image

        text = "Hello, World!\nThis is a test."
        result = await render_text_to_image(text)

        assert isinstance(result, bytes)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    @pytest.mark.asyncio
    async def test_render_multiline_text(self) -> None:
        """Render multiline text."""
        from opencode_on_im.renderers.image import render_text_to_image

        lines = ["Line " + str(i) for i in range(20)]
        text = "\n".join(lines)
        result = await render_text_to_image(text)

        assert isinstance(result, bytes)
        assert len(result) > 0


# ============================================================================
# Test: ContentRenderer (with mocked Settings)
# ============================================================================


def create_mock_settings(threshold: int = 10) -> MagicMock:
    """Create a mock Settings object."""
    mock = MagicMock()
    mock.message_image_threshold = threshold
    mock.image_width = 720
    mock.image_font_size = 13
    return mock


class TestContentRenderer:
    """Tests for ContentRenderer class."""

    @pytest.mark.asyncio
    async def test_short_content_returns_text(self) -> None:
        """Content below threshold returns as text."""
        from opencode_on_im.renderers.image import ContentRenderer

        renderer = ContentRenderer(create_mock_settings())
        content = "Short text\nJust a few lines"
        result = await renderer.render(content)

        assert result.is_image is False
        assert result.content == content
        assert result.caption is None

    @pytest.mark.asyncio
    async def test_long_content_returns_image(self) -> None:
        """Content exceeding threshold returns as image."""
        from opencode_on_im.renderers.image import ContentRenderer

        renderer = ContentRenderer(create_mock_settings())
        lines = ["Line " + str(i) for i in range(15)]
        content = "\n".join(lines)
        result = await renderer.render(content)

        assert result.is_image is True
        assert isinstance(result.content, bytes)
        assert result.content[:8] == b"\x89PNG\r\n\x1a\n"
        assert result.caption is not None
        assert "15 lines" in result.caption

    @pytest.mark.asyncio
    async def test_code_block_extraction(self) -> None:
        """Extract and render code blocks from markdown."""
        from opencode_on_im.renderers.image import ContentRenderer

        renderer = ContentRenderer(create_mock_settings())
        # Code block with 12 lines to exceed threshold of 10
        content = '''```python
def factorial(n):
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def main():
    for i in range(10):
        result = factorial(i)
        print(f"{i}! = {result}")

if __name__ == "__main__":
    main()
```
'''
        result = await renderer.render(content)

        assert result.is_image is True
        assert result.language == "python"
        assert "Python" in result.caption

    @pytest.mark.asyncio
    async def test_should_render_as_image(self) -> None:
        """Test threshold checking method."""
        from opencode_on_im.renderers.image import ContentRenderer

        renderer = ContentRenderer(create_mock_settings())
        short = "One\nTwo\nThree"
        long_content = "\n".join(["Line"] * 20)

        assert renderer.should_render_as_image(short) is False
        assert renderer.should_render_as_image(long_content) is True

    @pytest.mark.asyncio
    async def test_force_render_code(self) -> None:
        """Force render code to image regardless of length."""
        from opencode_on_im.renderers.image import ContentRenderer

        renderer = ContentRenderer(create_mock_settings())
        code = "print('short')"
        result = await renderer.render_code(code, language="python")

        assert isinstance(result, bytes)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    @pytest.mark.asyncio
    async def test_force_render_text(self) -> None:
        """Force render text to image regardless of length."""
        from opencode_on_im.renderers.image import ContentRenderer

        renderer = ContentRenderer(create_mock_settings())
        text = "Short text"
        result = await renderer.render_text(text)

        assert isinstance(result, bytes)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"


# ============================================================================
# Test: Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_content(self) -> None:
        """Empty content returns as text."""
        from opencode_on_im.renderers.image import ContentRenderer

        renderer = ContentRenderer(create_mock_settings())
        result = await renderer.render("")

        assert result.is_image is False
        assert result.content == ""

    @pytest.mark.asyncio
    async def test_single_line(self) -> None:
        """Single line never triggers image rendering."""
        from opencode_on_im.renderers.image import ContentRenderer

        renderer = ContentRenderer(create_mock_settings())
        result = await renderer.render("Just one line")

        assert result.is_image is False

    @pytest.mark.asyncio
    async def test_unicode_content(self) -> None:
        """Unicode content renders correctly."""
        from opencode_on_im.renderers.image import ContentRenderer

        renderer = ContentRenderer(create_mock_settings())
        content = "Hello\n" * 15
        result = await renderer.render(content)

        assert result.is_image is True
        assert isinstance(result.content, bytes)

    @pytest.mark.asyncio
    async def test_special_characters(self) -> None:
        """Special characters in code don't break rendering."""
        from opencode_on_im.renderers.image import render_code_to_image

        code = 's = "Hello <world>"'
        result = await render_code_to_image(code, language="python")

        assert isinstance(result, bytes)
        assert len(result) > 0
