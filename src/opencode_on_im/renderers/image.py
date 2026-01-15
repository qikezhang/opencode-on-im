"""Image rendering for code and text content.

Converts long code blocks or text to PNG images optimized for mobile viewing.
Uses Pygments for syntax highlighting and Pillow for image generation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import TextLexer, get_lexer_by_name, guess_lexer
from pygments.styles import get_style_by_name

if TYPE_CHECKING:
    from opencode_on_im.core.config import Settings


# Mobile-optimized dimensions
DEFAULT_WIDTH = 720  # Optimized for mobile portrait (most common viewing mode)
MAX_WIDTH = 1080  # Maximum width for larger displays
MIN_WIDTH = 480  # Minimum width for small screens
DEFAULT_FONT_SIZE = 13  # Slightly smaller for mobile readability
DEFAULT_LINE_HEIGHT = 1.4  # Better line spacing for mobile
DEFAULT_STYLE = "monokai"  # Dark theme, easy on eyes

# Code block regex pattern (markdown fenced code blocks)
CODE_BLOCK_PATTERN = re.compile(
    r"```(\w+)?\n(.*?)```",
    re.DOTALL | re.MULTILINE,
)


@dataclass
class RenderResult:
    """Result of content rendering."""

    is_image: bool
    content: bytes | str  # PNG bytes if is_image else original text
    caption: str | None = None  # Short summary when image
    language: str | None = None  # Detected language for code


@dataclass
class CodeBlock:
    """Extracted code block from markdown."""

    code: str
    language: str | None
    start_pos: int
    end_pos: int


class ContentRenderer:
    """Renders content to images when exceeding line threshold.

    Main entry point for the rendering system. Automatically decides
    whether to convert content to image based on line count.

    Usage:
        renderer = ContentRenderer(settings)
        result = await renderer.render(content)
        if result.is_image:
            await bot.send_photo(user_id, result.content, caption=result.caption)
        else:
            await bot.send_text(user_id, result.content)
    """

    def __init__(self, settings: Settings) -> None:
        self.threshold = settings.message_image_threshold
        self.style = DEFAULT_STYLE
        self.font_size = getattr(settings, 'image_font_size', DEFAULT_FONT_SIZE)
        self.width = getattr(settings, 'image_width', DEFAULT_WIDTH)

    async def render(self, content: str) -> RenderResult:
        """Render content, converting to image if exceeds threshold.

        Args:
            content: Text or markdown content to render

        Returns:
            RenderResult with either original text or PNG image bytes
        """
        # Check for code blocks first
        code_blocks = self._extract_code_blocks(content)

        if code_blocks:
            # Render the largest code block as image if it exceeds threshold
            largest_block = max(code_blocks, key=lambda b: b.code.count("\n"))
            line_count = largest_block.code.count("\n") + 1

            if line_count >= self.threshold:
                image_bytes = await render_code_to_image(
                    largest_block.code,
                    language=largest_block.language,
                    style=self.style,
                    font_size=self.font_size,
                )
                return RenderResult(
                    is_image=True,
                    content=image_bytes,
                    caption=self._generate_caption(largest_block.code, largest_block.language),
                    language=largest_block.language,
                )

        # Check plain text line count
        line_count = content.count("\n") + 1
        if line_count >= self.threshold:
            image_bytes = await render_text_to_image(
                content,
                max_width=self.width,
                font_size=self.font_size,
            )
            return RenderResult(
                is_image=True,
                content=image_bytes,
                caption=self._generate_caption(content),
            )

        # Return as-is
        return RenderResult(is_image=False, content=content)

    async def render_code(
        self,
        code: str,
        language: str | None = None,
    ) -> bytes:
        """Force render code to image regardless of threshold.

        Args:
            code: Source code to render
            language: Programming language for syntax highlighting

        Returns:
            PNG image bytes
        """
        return await render_code_to_image(
            code,
            language=language,
            style=self.style,
            font_size=self.font_size,
        )

    async def render_text(self, text: str) -> bytes:
        """Force render text to image regardless of threshold.

        Args:
            text: Plain text to render

        Returns:
            PNG image bytes
        """
        return await render_text_to_image(
            text,
            max_width=self.width,
            font_size=self.font_size,
        )

    def should_render_as_image(self, content: str) -> bool:
        """Check if content should be rendered as image.

        Args:
            content: Text content to check

        Returns:
            True if line count exceeds threshold
        """
        line_count = content.count("\n") + 1
        return line_count >= self.threshold

    def _extract_code_blocks(self, content: str) -> list[CodeBlock]:
        """Extract markdown code blocks from content."""
        blocks: list[CodeBlock] = []
        for match in CODE_BLOCK_PATTERN.finditer(content):
            language = match.group(1)  # May be None
            code = match.group(2).strip()
            blocks.append(
                CodeBlock(
                    code=code,
                    language=language,
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
            )
        return blocks

    def _generate_caption(
        self,
        content: str,
        language: str | None = None,
    ) -> str:
        """Generate a smart caption for the image.

        Analyzes content to provide meaningful context:
        - For code: language, line count, detected patterns
        - For text: summary of content type

        Args:
            content: Original content
            language: Programming language if known

        Returns:
            Caption string (max 200 chars)
        """
        line_count = content.count("\n") + 1
        char_count = len(content)

        # Try to detect content type and generate smart caption
        if language:
            # Code with known language
            summary = self._summarize_code(content, language)
            if summary:
                return f"{language.title()}: {summary} ({line_count} lines)"
            return f"{language.title()} code ({line_count} lines, {char_count:,} chars)"

        # Try to auto-detect content type
        content_type = self._detect_content_type(content)

        if content_type == "error":
            # Extract first error line
            first_line = content.split("\n")[0][:50]
            return f"Error output: {first_line}... ({line_count} lines)"

        if content_type == "json":
            return f"JSON data ({line_count} lines, {char_count:,} chars)"

        if content_type == "log":
            return f"Log output ({line_count} lines)"

        if content_type == "diff":
            # Count additions and deletions
            additions = content.count("\n+")
            deletions = content.count("\n-")
            return f"Diff: +{additions}/-{deletions} lines"

        if content_type == "command_output":
            return f"Command output ({line_count} lines)"

        # Default
        return f"Output ({line_count} lines, {char_count:,} chars)"

    def _summarize_code(self, code: str, language: str) -> str | None:
        """Generate a brief summary of code content.

        Returns None if no meaningful summary can be generated.
        """
        lines = code.split("\n")

        # Python: Look for function/class definitions
        if language.lower() in ("python", "py"):
            funcs = [ln for ln in lines if ln.strip().startswith("def ")]
            classes = [ln for ln in lines if ln.strip().startswith("class ")]
            if classes:
                class_name = classes[0].split("class ")[1].split("(")[0].split(":")[0]
                return f"class {class_name}"
            if funcs:
                func_name = funcs[0].split("def ")[1].split("(")[0]
                return f"function {func_name}"

        # JavaScript/TypeScript: Look for exports, functions
        if language.lower() in ("javascript", "js", "typescript", "ts", "tsx", "jsx"):
            for line in lines[:10]:
                if "export default" in line or "export function" in line:
                    return "module export"
                if "function " in line or "const " in line and "=>" in line:
                    return "function"
                if "class " in line:
                    return "class definition"

        # Go: Look for func/type definitions
        if language.lower() == "go":
            for line in lines[:10]:
                if line.startswith("func "):
                    func_name = line.split("func ")[1].split("(")[0]
                    return f"func {func_name}"
                if line.startswith("type "):
                    return "type definition"

        # Rust: Look for fn/struct/impl
        if language.lower() in ("rust", "rs"):
            for line in lines[:10]:
                if line.strip().startswith("fn "):
                    return "function"
                if line.strip().startswith("struct "):
                    return "struct definition"
                if line.strip().startswith("impl "):
                    return "implementation"

        return None

    def _detect_content_type(self, content: str) -> str:
        """Detect the type of content for better captioning."""
        lines = content.split("\n")
        first_line = lines[0] if lines else ""

        # Error patterns
        error_patterns = ["error:", "Error:", "ERROR", "exception", "Exception", "Traceback"]
        if any(pattern in content[:500] for pattern in error_patterns):
            return "error"

        # JSON
        stripped = content.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or \
           (stripped.startswith("[") and stripped.endswith("]")):
            return "json"

        # Diff
        if content.startswith("diff ") or content.startswith("---") or \
           content.count("\n+") > 2 and content.count("\n-") > 2:
            return "diff"

        # Log output (timestamps, log levels)
        log_patterns = ["INFO", "DEBUG", "WARN", "ERROR", "[20", "2024-", "2025-", "2026-"]
        if any(pattern in first_line for pattern in log_patterns):
            return "log"

        # Command output (starts with $ or >)
        if first_line.startswith("$ ") or first_line.startswith("> "):
            return "command_output"

        return "text"


async def render_code_to_image(
    code: str,
    language: str | None = None,
    style: str = DEFAULT_STYLE,
    font_size: int = DEFAULT_FONT_SIZE,
    line_numbers: bool = True,
) -> bytes:
    """Render code with syntax highlighting to PNG image.

    Uses Pygments for syntax highlighting with a dark theme optimized
    for mobile viewing.

    Args:
        code: Source code to render
        language: Programming language (auto-detected if None)
        style: Pygments style name (default: monokai)
        font_size: Font size in pixels
        line_numbers: Show line numbers

    Returns:
        PNG image bytes
    """
    # Get lexer for syntax highlighting
    try:
        lexer = get_lexer_by_name(language.lower()) if language else guess_lexer(code)
    except Exception:
        lexer = TextLexer()

    # Configure formatter for mobile-friendly output
    formatter = ImageFormatter(
        style=get_style_by_name(style),
        font_size=font_size,
        line_numbers=line_numbers,
        line_number_bg="#2d2d2d",
        line_number_fg="#888888",
        line_number_separator=True,
        image_pad=20,
    )

    # Generate highlighted image
    image_data: bytes = highlight(code, lexer, formatter)
    return image_data


async def render_text_to_image(
    text: str,
    max_width: int = DEFAULT_WIDTH,
    font_size: int = DEFAULT_FONT_SIZE,
    bg_color: str = "#1e1e1e",
    text_color: str = "#d4d4d4",
    padding: int = 20,
) -> bytes:
    """Render plain text to PNG image.

    Creates a simple image with the text content, useful for
    non-code content that exceeds the line threshold.

    Args:
        text: Text content to render
        max_width: Maximum image width in pixels
        font_size: Font size in pixels
        bg_color: Background color (hex)
        text_color: Text color (hex)
        padding: Padding around text in pixels

    Returns:
        PNG image bytes
    """
    # Try to load a monospace font, fall back to default
    font: FreeTypeFont | ImageFont.ImageFont
    try:
        # Try common monospace fonts
        for font_name in [
            "DejaVuSansMono.ttf",
            "Menlo.ttc",
            "Consolas.ttf",
            "Monaco.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except OSError:
                continue
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Calculate dimensions
    lines = text.split("\n")
    line_height = font_size + 4

    # Word wrap long lines
    wrapped_lines: list[str] = []
    for line in lines:
        if len(line) > 100:  # Approximate character limit per line
            # Simple word wrap
            words = line.split(" ")
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > 100:
                    wrapped_lines.append(current_line)
                    current_line = word
                else:
                    current_line = f"{current_line} {word}" if current_line else word
            if current_line:
                wrapped_lines.append(current_line)
        else:
            wrapped_lines.append(line)

    # Calculate final dimensions
    width = max_width
    height = len(wrapped_lines) * line_height + (padding * 2)

    # Ensure minimum height
    height = max(height, 100)

    # Create image
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw text
    y = padding
    for line in wrapped_lines:
        draw.text((padding, y), line, fill=text_color, font=font)
        y += line_height

    # Save to bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


# Convenience function for quick rendering
async def render_content(content: str, threshold: int = 10) -> RenderResult:
    """Quick render without Settings object.

    Args:
        content: Text to render
        threshold: Line count threshold for image conversion

    Returns:
        RenderResult with text or image
    """
    from opencode_on_im.core.config import Settings

    settings = Settings(message_image_threshold=threshold)
    renderer = ContentRenderer(settings)
    return await renderer.render(content)
