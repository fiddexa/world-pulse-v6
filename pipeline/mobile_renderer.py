from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from PIL import Image, ImageDraw, ImageFont, ImageOps


# =====================================================================
# BRAND / LAYOUT
# =====================================================================

BRAND_NAME = "AROUND THE MAIN"
TELEGRAM_HANDLE = "@aroundthemain"

RED = (190, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (105, 105, 105)
LIGHT_GRAY = (225, 225, 225)

WIDTH = 900
MARGIN = 36
CARD_GAP = 28

LOGO_PATH = Path("assets/logo.png")


# =====================================================================
# HELPERS
# =====================================================================

def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []

    if bold:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            ]
        )

    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)

    return ImageFont.load_default()


def _list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


def _title(event: dict) -> str:
    for key in (
        "title",
        "headline",
        "publication_title",
        "display_title",
    ):
        value = _safe_text(event.get(key))
        if value:
            return value

    return "Untitled story"


def _summary(event: dict) -> str:
    for key in (
        "summary",
        "publication_summary",
        "description",
        "dek",
    ):
        value = _safe_text(event.get(key))
        if value:
            return value

    return ""


def _why_it_matters(event: dict) -> str:
    content = event.get("content")

    if not isinstance(content, dict):
        return ""

    return _safe_text(
        content.get("why_it_matters")
    )


def _sources(event: dict) -> list[str]:
    value = event.get("sources")

    if isinstance(value, list):
        result = []

        for item in value:
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, dict):
                text = (
                    _safe_text(item.get("name"))
                    or _safe_text(item.get("title"))
                    or _safe_text(item.get("url"))
                )
            else:
                text = _safe_text(item)

            if text:
                result.append(text)

        return result

    if isinstance(value, str) and value.strip():
        return [value.strip()]

    return []


def _image_path(event: dict) -> Path | None:
    for key in (
        "image_path",
        "local_image",
        "image",
        "photo_path",
    ):
        value = event.get(key)

        if not value:
            continue

        path = Path(str(value))

        if path.exists() and path.is_file():
            return path

    return None


def _load_image(
    event: dict,
    width: int,
    height: int,
) -> Image.Image:

    path = _image_path(event)

    if path is not None:
        try:
            with Image.open(path) as source:
                return ImageOps.fit(
                    source.convert("RGB"),
                    (width, height),
                    method=Image.Resampling.LANCZOS,
                )
        except Exception:
            pass

    image = Image.new(
        "RGB",
        (width, height),
        LIGHT_GRAY,
    )

    draw = ImageDraw.Draw(image)

    text = "AROUND\nTHE MAIN"

    bbox = draw.multiline_textbbox(
        (0, 0),
        text,
        font=_font(34, bold=True),
        spacing=4,
    )

    draw.multiline_text(
        (
            (width - (bbox[2] - bbox[0])) / 2,
            (height - (bbox[3] - bbox[1])) / 2,
        ),
        text,
        font=_font(34, bold=True),
        fill=GRAY,
        spacing=4,
        align="center",
    )

    return image


def _wrap(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:

    words = text.split()

    if not words:
        return []

    lines = []
    current = ""

    for word in words:
        candidate = (
            word
            if not current
            else f"{current} {word}"
        )

        bbox = draw.textbbox(
            (0, 0),
            candidate,
            font=font,
        )

        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return lines


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill,
    max_width: int,
    max_lines: int | None = None,
    spacing: int = 8,
) -> int:

    lines = _wrap(
        draw,
        text,
        font,
        max_width,
    )

    if max_lines is not None:
        lines = lines[:max_lines]

    line_height = (
        font.getbbox("Ag")[3]
        - font.getbbox("Ag")[1]
        + spacing
    )

    for line in lines:
        draw.text(
            (x, y),
            line,
            font=font,
            fill=fill,
        )
        y += line_height

    return y


def _edition_label(edition: dict) -> str:
    value = _safe_text(
        edition.get("edition_label")
    )

    if value:
        return value

    number = edition.get("edition_number")

    if isinstance(number, int):
        return f"EDITION {number:04d}"

    if isinstance(number, str) and number.isdigit():
        return f"EDITION {int(number):04d}"

    return "EDITION 0001"


def _edition_date(edition: dict) -> str:
    for key in (
        "publication_date",
        "edition_date",
        "date",
    ):
        value = _safe_text(edition.get(key))
        if value:
            return value

    return ""


def _format_date(value: str) -> str:
    if not value:
        return ""

    # Keep the renderer deliberately conservative.
    # If the upstream edition already contains a display date,
    # use it unchanged.
    return value


def _collect_events(edition: dict) -> list[dict]:
    result = []

    seen = set()

    top = edition.get("top_story")

    if isinstance(top, dict):
        result.append(top)
        seen.add(id(top))

    for key in (
        "main_stories",
        "briefs",
        "additional_events",
        "remaining_events",
        "overflow_events",
    ):
        for event in _list(
            edition.get(key)
        ):
            if not isinstance(event, dict):
                continue

            if id(event) in seen:
                continue

            result.append(event)
            seen.add(id(event))

    return result


def _event_category(event: dict) -> str:
    for key in (
        "category",
        "section",
        "topic",
    ):
        value = _safe_text(event.get(key))

        if value:
            return value.upper()

    return "WORLD"


# =====================================================================
# CARD HEIGHT
# =====================================================================


def _card_height(event: dict) -> int:
    """
    Calculate card height from the actual amount of content.

    The mobile renderer uses the same editorial fields as the edition,
    but reserves enough vertical space for every rendered section.
    """

    dummy = Image.new("RGB", (WIDTH, 2000), WHITE)
    draw = ImageDraw.Draw(dummy)

    text_width = WIDTH - MARGIN * 2 - 32

    title_lines = _wrap(
        draw,
        _title(event),
        _font(32, bold=True),
        text_width,
    )[:4]

    summary_lines = _wrap(
        draw,
        _summary(event),
        _font(17),
        text_width,
    )[:5]

    why_lines = _wrap(
        draw,
        _why_it_matters(event),
        _font(15),
        text_width - 14,
    )[:3]

    sources_text = "  •  ".join(_sources(event)[:3])

    source_lines = _wrap(
        draw,
        sources_text,
        _font(10),
        max(1, text_width - 70),
    )[:2]

    title_line_h = 40
    summary_line_h = 30
    why_line_h = 25
    source_line_h = 16

    height = 58 + 300 + 22

    height += max(1, len(title_lines)) * title_line_h
    height += 14

    if summary_lines:
        height += len(summary_lines) * summary_line_h
        height += 18

    if why_lines:
        height += 23
        height += len(why_lines) * why_line_h
        height += 18

    if source_lines:
        height += 32
        height += len(source_lines) * source_line_h
        height += 20

    return max(height, 470)

# =====================================================================
# MOBILE EDITION
# =====================================================================


def render_mobile_edition(
    edition: dict,
    output_path: str | Path,
) -> Path:

    if not isinstance(edition, dict):
        raise ValueError(
            "edition must be a dictionary"
        )

    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    events = _collect_events(edition)

    header_height = 245
    footer_height = 150

    card_heights = [
        _card_height(event)
        for event in events
    ]

    total_height = (
        MARGIN
        + header_height
        + 10
        + sum(card_heights)
        + CARD_GAP * max(0, len(events) - 1)
        + footer_height
        + MARGIN
    )

    total_height = max(total_height, 900)

    canvas = Image.new(
        "RGB",
        (WIDTH, total_height),
        WHITE,
    )

    draw = ImageDraw.Draw(canvas)

    # ================================================================
    # HEADER
    # ================================================================

    y = MARGIN

    if LOGO_PATH.exists():
        try:
            with Image.open(LOGO_PATH) as source:
                logo = ImageOps.contain(
                    source.convert("RGB"),
                    (120, 120),
                    Image.Resampling.LANCZOS,
                )

                canvas.paste(
                    logo,
                    (MARGIN, y),
                )
        except Exception:
            pass

    brand_x = MARGIN + 140

    draw.text(
        (brand_x, y + 8),
        "AROUND",
        font=_font(42, bold=True),
        fill=BLACK,
    )

    draw.text(
        (brand_x, y + 52),
        "THE MAIN",
        font=_font(42, bold=True),
        fill=RED,
    )

    draw.text(
        (brand_x, y + 103),
        "GLOBAL NEWS",
        font=_font(17, bold=True),
        fill=BLACK,
    )

    edition_label = _edition_label(edition)

    draw.text(
        (MARGIN, y + 142),
        edition_label,
        font=_font(18, bold=True),
        fill=RED,
    )

    date_text = _format_date(
        _edition_date(edition)
    )

    if date_text:
        draw.text(
            (MARGIN, y + 169),
            date_text,
            font=_font(15, bold=True),
            fill=BLACK,
        )

    draw.line(
        (
            MARGIN,
            header_height - 18,
            WIDTH - MARGIN,
            header_height - 18,
        ),
        fill=BLACK,
        width=5,
    )

    y = header_height + 10

    # ================================================================
    # NEWS CARDS
    # ================================================================

    for index, event in enumerate(events):

        card_height = card_heights[index]

        card_top = y
        card_bottom = y + card_height

        draw.rectangle(
            (
                MARGIN,
                card_top,
                WIDTH - MARGIN,
                card_bottom,
            ),
            outline=BLACK,
            width=2,
        )

        # Category header.
        category = _event_category(event)

        draw.rectangle(
            (
                MARGIN,
                card_top,
                WIDTH - MARGIN,
                card_top + 42,
            ),
            fill=BLACK,
        )

        draw.text(
            (
                MARGIN + 16,
                card_top + 9,
            ),
            category,
            font=_font(16, bold=True),
            fill=WHITE,
        )

        # Story number, not category number.
        number_text = f"{index + 1:02d}"

        bbox = draw.textbbox(
            (0, 0),
            number_text,
            font=_font(16, bold=True),
        )

        draw.text(
            (
                WIDTH
                - MARGIN
                - 16
                - (bbox[2] - bbox[0]),
                card_top + 9,
            ),
            number_text,
            font=_font(16, bold=True),
            fill=RED,
        )

        # Image.
        image_top = card_top + 58
        image_height = 255

        image = _load_image(
            event,
            WIDTH - MARGIN * 2 - 32,
            image_height,
        )

        canvas.paste(
            image,
            (
                MARGIN + 16,
                image_top,
            ),
        )

        text_x = MARGIN + 16
        text_width = WIDTH - MARGIN * 2 - 32

        title_y = image_top + image_height + 22

        title_end = _draw_wrapped(
            draw,
            _title(event),
            text_x,
            title_y,
            _font(29, bold=True),
            BLACK,
            text_width,
            max_lines=4,
            spacing=5,
        )

        current_y = title_end + 12

        # Summary.
        summary = _summary(event)

        if summary:
            summary_end = _draw_wrapped(
                draw,
                summary,
                text_x,
                current_y,
                _font(18),
                GRAY,
                text_width,
                max_lines=5,
                spacing=5,
            )

            current_y = summary_end + 18

        # Why it matters.
        why = _why_it_matters(event)

        if why:
            why_top = current_y

            draw.rectangle(
                (
                    text_x,
                    why_top,
                    text_x + 5,
                    why_top + 66,
                ),
                fill=RED,
            )

            draw.text(
                (
                    text_x + 14,
                    why_top,
                ),
                "WHY IT MATTERS",
                font=_font(13, bold=True),
                fill=RED,
            )

            why_end = _draw_wrapped(
                draw,
                why,
                text_x + 14,
                why_top + 23,
                _font(16),
                BLACK,
                text_width - 14,
                max_lines=3,
                spacing=4,
            )

            current_y = why_end + 18

        # Sources are positioned AFTER all content.
        sources = _sources(event)

        if sources:
            sources_y = current_y

            draw.text(
                (
                    text_x,
                    sources_y,
                ),
                "SOURCES",
                font=_font(11, bold=True),
                fill=RED,
            )

            source_text = "  •  ".join(
                sources[:3]
            )

            _draw_wrapped(
                draw,
                source_text,
                text_x + 70,
                sources_y - 2,
                _font(10),
                GRAY,
                text_width - 70,
                max_lines=2,
                spacing=2,
            )

        # The calculated card height guarantees that the next card
        # starts after the current card's actual content area.
        y = card_bottom + CARD_GAP

    # ================================================================
    # FOOTER
    # ================================================================

    footer_top = total_height - footer_height

    draw.line(
        (
            MARGIN,
            footer_top,
            WIDTH - MARGIN,
            footer_top,
        ),
        fill=BLACK,
        width=3,
    )

    draw.text(
        (
            MARGIN,
            footer_top + 22,
        ),
        "DAILY BRIEF",
        font=_font(18, bold=True),
        fill=RED,
    )

    draw.text(
        (
            MARGIN,
            footer_top + 53,
        ),
        "The most important stories, delivered in brief.",
        font=_font(14),
        fill=BLACK,
    )

    draw.text(
        (
            MARGIN,
            footer_top + 79,
        ),
        "Three times daily  •  7:00  |  13:00  |  20:00",
        font=_font(12, bold=True),
        fill=GRAY,
    )

    draw.text(
        (
            MARGIN,
            footer_top + 111,
        ),
        f"🎧  {TELEGRAM_HANDLE}",
        font=_font(13, bold=True),
        fill=BLACK,
    )

    draw.rectangle(
        (
            0,
            total_height - 24,
            WIDTH,
            total_height,
        ),
        fill=RED,
    )

    tagline = "STAY INFORMED. STAY AHEAD."

    bbox = draw.textbbox(
        (0, 0),
        tagline,
        font=_font(13, bold=True),
    )

    draw.text(
        (
            (WIDTH - (bbox[2] - bbox[0])) / 2,
            total_height - 21,
        ),
        tagline,
        font=_font(13, bold=True),
        fill=WHITE,
    )

    canvas.save(
        output,
        format="PNG",
        optimize=True,
    )

    return output


    if not isinstance(edition, dict):
        raise ValueError(
            "edition must be a dictionary"
        )

    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    events = _collect_events(edition)

    card_heights = [
        _card_height(event)
        for event in events
    ]

    header_height = 245

    footer_height = 150

    total_height = (
        header_height
        + footer_height
        + sum(card_heights)
        + CARD_GAP * max(0, len(events) - 1)
        + MARGIN * 2
    )

    total_height = max(
        total_height,
        900,
    )

    canvas = Image.new(
        "RGB",
        (WIDTH, total_height),
        WHITE,
    )

    draw = ImageDraw.Draw(canvas)

    # ================================================================
    # HEADER
    # ================================================================

    y = MARGIN

    if LOGO_PATH.exists():
        try:
            with Image.open(LOGO_PATH) as source:
                logo = ImageOps.contain(
                    source.convert("RGB"),
                    (120, 120),
                    Image.Resampling.LANCZOS,
                )

                canvas.paste(
                    logo,
                    (MARGIN, y),
                )
        except Exception:
            pass

    brand_x = MARGIN + 140

    draw.text(
        (brand_x, y + 8),
        "AROUND",
        font=_font(42, bold=True),
        fill=BLACK,
    )

    draw.text(
        (brand_x, y + 52),
        "THE MAIN",
        font=_font(42, bold=True),
        fill=RED,
    )

    draw.text(
        (brand_x, y + 103),
        "GLOBAL NEWS",
        font=_font(17, bold=True),
        fill=BLACK,
    )

    edition_label = _edition_label(
        edition
    )

    draw.text(
        (MARGIN, y + 142),
        edition_label,
        font=_font(18, bold=True),
        fill=RED,
    )

    date_text = _format_date(
        _edition_date(edition)
    )

    if date_text:
        draw.text(
            (
                MARGIN,
                y + 169,
            ),
            date_text,
            font=_font(15, bold=True),
            fill=BLACK,
        )

    draw.line(
        (
            MARGIN,
            header_height - 18,
            WIDTH - MARGIN,
            header_height - 18,
        ),
        fill=BLACK,
        width=5,
    )

    y = header_height + 10

    # ================================================================
    # NEWS CARDS
    # ================================================================

    for index, event in enumerate(events):

        card_height = card_heights[index]

        card_top = y
        card_bottom = y + card_height

        # Card frame.
        draw.rectangle(
            (
                MARGIN,
                card_top,
                WIDTH - MARGIN,
                card_bottom,
            ),
            outline=BLACK,
            width=2,
        )

        # Category strip.
        category = _event_category(event)

        draw.rectangle(
            (
                MARGIN,
                card_top,
                WIDTH - MARGIN,
                card_top + 42,
            ),
            fill=BLACK,
        )

        draw.text(
            (
                MARGIN + 16,
                card_top + 9,
            ),
            category,
            font=_font(16, bold=True),
            fill=WHITE,
        )

        # Number.
        number_text = f"{index + 1:02d}"

        bbox = draw.textbbox(
            (0, 0),
            number_text,
            font=_font(16, bold=True),
        )

        draw.text(
            (
                WIDTH
                - MARGIN
                - 16
                - (bbox[2] - bbox[0]),
                card_top + 9,
            ),
            number_text,
            font=_font(16, bold=True),
            fill=RED,
        )

        # Image.
        image_top = card_top + 58
        image_height = 300

        image = _load_image(
            event,
            WIDTH - MARGIN * 2 - 32,
            image_height,
        )

        canvas.paste(
            image,
            (
                MARGIN + 16,
                image_top,
            ),
        )

        text_x = MARGIN + 16
        text_width = WIDTH - MARGIN * 2 - 32

        title_y = image_top + image_height + 22

        # Headline.
        title_end = _draw_wrapped(
            draw,
            _title(event),
            text_x,
            title_y,
            _font(29, bold=True),
            BLACK,
            text_width,
            max_lines=4,
            spacing=5,
        )

        # Summary.
        summary = _summary(event)

        if summary:
            summary_y = title_end + 12

            summary_end = _draw_wrapped(
                draw,
                summary,
                text_x,
                summary_y,
                _font(17),
                GRAY,
                text_width,
                max_lines=5,
                spacing=5,
            )
        else:
            summary_end = title_end

        # Why it matters.
        why = _why_it_matters(event)

        if why:
            why_top = summary_end + 18

            draw.rectangle(
                (
                    text_x,
                    why_top,
                    text_x + 5,
                    why_top + 66,
                ),
                fill=RED,
            )

            draw.text(
                (
                    text_x + 14,
                    why_top,
                ),
                "WHY IT MATTERS",
                font=_font(13, bold=True),
                fill=RED,
            )

            _draw_wrapped(
                draw,
                why,
                text_x + 14,
                why_top + 23,
                _font(15),
                BLACK,
                text_width - 14,
                max_lines=3,
                spacing=4,
            )

        # Sources.
        sources = _sources(event)

        if sources:
            sources_y = card_bottom - 58

            draw.text(
                (
                    text_x,
                    sources_y,
                ),
                "SOURCES",
                font=_font(11, bold=True),
                fill=RED,
            )

            source_text = "  •  ".join(
                sources[:3]
            )

            _draw_wrapped(
                draw,
                source_text,
                text_x + 70,
                sources_y - 2,
                _font(10),
                GRAY,
                text_width - 70,
                max_lines=2,
                spacing=2,
            )

        y = card_bottom + CARD_GAP

    # ================================================================
    # FOOTER
    # ================================================================

    footer_top = total_height - footer_height

    draw.line(
        (
            MARGIN,
            footer_top,
            WIDTH - MARGIN,
            footer_top,
        ),
        fill=BLACK,
        width=3,
    )

    draw.text(
        (
            MARGIN,
            footer_top + 22,
        ),
        "DAILY BRIEF",
        font=_font(18, bold=True),
        fill=RED,
    )

    draw.text(
        (
            MARGIN,
            footer_top + 53,
        ),
        "The most important stories, delivered in brief.",
        font=_font(14),
        fill=BLACK,
    )

    draw.text(
        (
            MARGIN,
            footer_top + 79,
        ),
        "Three times daily  •  7:00  |  13:00  |  20:00",
        font=_font(12, bold=True),
        fill=GRAY,
    )

    draw.text(
        (
            MARGIN,
            footer_top + 111,
        ),
        f"🎧  {TELEGRAM_HANDLE}",
        font=_font(13, bold=True),
        fill=BLACK,
    )

    draw.rectangle(
        (
            0,
            total_height - 24,
            WIDTH,
            total_height,
        ),
        fill=RED,
    )

    tagline = "STAY INFORMED. STAY AHEAD."

    bbox = draw.textbbox(
        (0, 0),
        tagline,
        font=_font(13, bold=True),
    )

    draw.text(
        (
            (WIDTH - (bbox[2] - bbox[0])) / 2,
            total_height - 21,
        ),
        tagline,
        font=_font(13, bold=True),
        fill=WHITE,
    )

    canvas.save(
        output,
        format="PNG",
        optimize=True,
    )

    return output
