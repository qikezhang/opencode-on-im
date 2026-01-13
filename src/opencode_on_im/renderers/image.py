from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.styles import get_style_by_name


async def render_code_to_image(
    code: str,
    language: str | None = None,
    style: str = "monokai",
    font_size: int = 14,
) -> bytes:
    try:
        if language:
            lexer = get_lexer_by_name(language)
        else:
            lexer = guess_lexer(code)
    except Exception:
        from pygments.lexers import TextLexer
        lexer = TextLexer()

    formatter = ImageFormatter(
        style=get_style_by_name(style),
        font_size=font_size,
        line_numbers=True,
        line_number_bg="#2d2d2d",
        line_number_fg="#888888",
    )

    image_data: bytes = highlight(code, lexer, formatter)

    return image_data


async def render_text_to_image(
    text: str,
    max_width: int = 800,
    font_size: int = 14,
    bg_color: str = "#1e1e1e",
    text_color: str = "#d4d4d4",
) -> bytes:
    font: FreeTypeFont | ImageFont.ImageFont
    try:
        font = ImageFont.truetype("DejaVuSansMono.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    lines = text.split("\n")
    line_height = font_size + 4

    width = max_width
    height = len(lines) * line_height + 40

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    y = 20
    for line in lines:
        draw.text((20, y), line, fill=text_color, font=font)
        y += line_height

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
