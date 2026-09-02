"""
AROUND THE MAIN — Newspaper Renderer V4

Automatic 3:4 smartphone newspaper layout.

Editorial logic is intentionally outside this module.
This renderer only turns an already-built edition into a visual page.

Image policy:
- uses only explicitly supplied local images;
- never downloads Reuters/AP/Bloomberg/etc. images;
- missing images use an AROUND THE MAIN branded placeholder.
"""

from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import html
import re

from PIL import Image, ImageDraw, ImageFont, ImageOps


# =====================================================================
# BRAND
# =====================================================================

BRAND_NAME = "AROUND THE MAIN"
GLOBAL_NEWS = "GLOBAL NEWS"
TAGLINE = "STAY INFORMED. STAY AHEAD."
SUBTITLE = "THE WORLD. THE MAIN. IN BRIEF."

TELEGRAM_HANDLE = "@aroundthemain"
X_HANDLE = "@aroundthemain"
INSTAGRAM_HANDLE = "@aroundthemain"

LOGO_PATH = Path("assets/logo.png")

COPYRIGHT = "© 2026 AROUND THE MAIN. All rights reserved."
LEGAL = (
    "News independently prepared from cited sources. "
    "Third-party trademarks and materials belong to their respective owners."
)


# =====================================================================
# PAGE
# =====================================================================

WIDTH = 1500
HEIGHT = 2000

MARGIN = 28
CONTENT_WIDTH = WIDTH - (MARGIN * 2)

WHITE = (250, 250, 248)
BLACK = (12, 12, 12)
RED = (198, 20, 30)
GRAY = (105, 105, 105)
LIGHT_GRAY = (215, 215, 212)


# =====================================================================
# FONTS
# =====================================================================

def _font(size: int, bold: bool = False):
    candidates = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]
    )

    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)

    return ImageFont.load_default()


# =====================================================================
# TEXT
# =====================================================================

def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _wrap(draw, text, font, width):
    text = _safe_text(text)

    if not text:
        return []

    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"

        bbox = draw.textbbox(
            (0, 0),
            candidate,
            font=font,
        )

        if bbox[2] - bbox[0] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def _draw_block(
    draw,
    text,
    x,
    y,
    font,
    fill,
    width,
    max_lines=None,
    spacing=4,
):
    lines = _wrap(
        draw,
        text,
        font,
        width,
    )

    if max_lines is not None:
        lines = lines[:max_lines]

    if not lines:
        return y

    bbox = draw.textbbox(
        (0, 0),
        "Ag",
        font=font,
    )

    line_height = (
        bbox[3] - bbox[1] + spacing
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


# =====================================================================
# EDITION DATA
# =====================================================================

def _list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _content(event):
    value = event.get("content")
    return value if isinstance(value, dict) else {}


def _publication(event):
    value = event.get("publication")
    return value if isinstance(value, dict) else {}


def _title(event):
    c = _content(event)

    return _safe_text(
        c.get("headline")
        or event.get("headline")
        or event.get("title")
        or event.get("original_title")
    )


def _summary(event):
    c = _content(event)

    return _safe_text(
        c.get("summary")
        or c.get("body")
        or c.get("text")
        or event.get("summary")
    )


def _why_it_matters(event):
    c = _content(event)

    return _safe_text(
        c.get("why_it_matters")
    )


def _sources(event):
    p = _publication(event)

    sources = p.get("sources")

    if isinstance(sources, list):
        values = [
            _safe_text(x)
            for x in sources
            if _safe_text(x)
        ]

        if values:
            return _normalize_sources(values)

    source = _safe_text(
        event.get("source")
    )

    if source:
        return _normalize_sources([source])

    return ""


def _normalize_sources(values):
    mapping = {
        "un": "United Nations",
        "uno": "United Nations",
        "united nations": "United Nations",
        "reuters": "Reuters",
        "ap": "AP",
        "ap news": "AP",
        "associated press": "AP",
    }

    result = []

    for value in values:
        clean = _safe_text(value)

        if not clean:
            continue

        result.append(
            mapping.get(
                clean.lower(),
                clean,
            )
        )

    result = list(dict.fromkeys(result))

    if not result:
        return ""

    return "Sources: " + " | ".join(result)


def _image_path(event):
    possible = [
        event.get("image_path"),
        event.get("image"),
        _content(event).get("image_path"),
        _content(event).get("image"),
    ]

    for value in possible:
        if value:
            path = Path(str(value))

            if path.exists():
                return path

    return None


# =====================================================================
# DATES / EDITION
# =====================================================================

def _edition_date(edition):
    value = _safe_text(
        edition.get("edition_date")
    )

    if value:
        return value

    edition_id = _safe_text(
        edition.get("edition_id")
    )

    match = re.search(
        r"(\d{4}-\d{2}-\d{2})",
        edition_id,
    )

    return (
        match.group(1)
        if match
        else ""
    )


def _edition_time(edition):
    return _safe_text(
        edition.get("edition_time")
        or edition.get("time")
    )


def _format_date(value):
    if not value:
        return ""

    try:
        parsed = datetime.strptime(
            value,
            "%Y-%m-%d",
        )

        return parsed.strftime(
            "%B %d, %Y"
        ).upper()

    except ValueError:
        return value.upper()


def _edition_label(edition):
    """
    Return the authoritative edition label supplied by production.

    The production scheduler owns edition numbering.
    The renderer must never create its own independent counter.
    """

    label = _safe_text(
        edition.get("edition_label")
    )

    if label:
        return label

    # Compatibility fallback for older/test editions that do not yet
    # contain edition_label.
    number = edition.get("edition_number")

    if number is not None:
        try:
            return f"EDITION {int(number):04d}"
        except (TypeError, ValueError):
            pass

    return "EDITION 0001"


# =====================================================================
# IMAGES
# =====================================================================

def _placeholder(width, height, label):
    image = Image.new(
        "RGB",
        (width, height),
        BLACK,
    )

    draw = ImageDraw.Draw(image)

    center_x = width // 2
    center_y = height // 2

    max_radius = min(
        width,
        height,
    ) // 3

    for radius in range(
        max_radius,
        20,
        -24,
    ):
        draw.ellipse(
            (
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
            ),
            outline=RED,
            width=2,
        )

    draw.line(
        (
            0,
            height,
            width,
            0,
        ),
        fill=RED,
        width=max(
            2,
            width // 180,
        ),
    )

    label = _safe_text(label).upper()

    font = _font(
        max(
            18,
            min(width, height) // 10,
        ),
        bold=True,
    )

    bbox = draw.textbbox(
        (0, 0),
        label,
        font=font,
    )

    draw.text(
        (
            center_x
            - (bbox[2] - bbox[0]) / 2,
            center_y
            - (bbox[3] - bbox[1]) / 2,
        ),
        label,
        font=font,
        fill=WHITE,
    )

    return image


def _load_image(event, width, height, label):
    path = _image_path(event)

    if path is None:
        return _placeholder(
            width,
            height,
            label,
        )

    try:
        with Image.open(path) as source:
            source = source.convert("RGB")

            return ImageOps.fit(
                source,
                (width, height),
                method=Image.Resampling.LANCZOS,
            )

    except Exception:
        return _placeholder(
            width,
            height,
            label,
        )


def _paste(canvas, event, box, label):
    left, top, right, bottom = box

    image = _load_image(
        event,
        right - left,
        bottom - top,
        label,
    )

    canvas.paste(
        image,
        (left, top),
    )


# =====================================================================
# MAIN
# =====================================================================

def render_newspaper(
    edition: Any,
    output_path: str | Path,
    page_number: int = 1,
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

    canvas = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        WHITE,
    )

    draw = ImageDraw.Draw(canvas)

    # ================================================================
    # HEADER
    # ================================================================

    logo_size = 250

    if LOGO_PATH.exists():
        with Image.open(LOGO_PATH) as source:
            logo = ImageOps.contain(
                source.convert("RGB"),
                (logo_size, logo_size),
                Image.Resampling.LANCZOS,
            )

            canvas.paste(
                logo,
                (
                    MARGIN,
                    20,
                ),
            )

    brand_x = 305

    draw.text(
        (brand_x, 35),
        "AROUND",
        font=_font(65, bold=True),
        fill=BLACK,
    )

    draw.text(
        (brand_x, 100),
        "THE MAIN",
        font=_font(65, bold=True),
        fill=RED,
    )

    draw.text(
        (brand_x, 172),
        GLOBAL_NEWS,
        font=_font(24, bold=True),
        fill=BLACK,
    )

    draw.line(
        (
            brand_x + 220,
            184,
            brand_x + 275,
            184,
        ),
        fill=RED,
        width=4,
    )

    draw.text(
        (brand_x + 292, 172),
        SUBTITLE,
        font=_font(18),
        fill=GRAY,
    )

    # Edition.
    edition_left = WIDTH - MARGIN - 300
    edition_top = 22
    edition_right = WIDTH - MARGIN
    edition_bottom = 172

    draw.rectangle(
        (
            edition_left,
            edition_top,
            edition_right,
            edition_bottom,
        ),
        fill=BLACK,
    )

    draw.rectangle(
        (
            edition_left,
            edition_top,
            edition_right,
            edition_top + 43,
        ),
        fill=RED,
    )

    draw.text(
        (
            edition_left + 18,
            edition_top + 8,
        ),
        "EDITION",
        font=_font(20, bold=True),
        fill=WHITE,
    )

    edition_label = _edition_label(
        edition
    )

    # Render only the numeric portion in the large edition box.
    number_match = re.search(
        r"(\d{4})$",
        edition_label,
    )

    number = (
        number_match.group(1)
        if number_match
        else edition_label
    )

    bbox = draw.textbbox(
        (0, 0),
        number,
        font=_font(58, bold=True),
    )

    draw.text(
        (
            edition_left
            + (
                300
                - (bbox[2] - bbox[0])
            ) / 2,
            edition_top + 53,
        ),
        number,
        font=_font(58, bold=True),
        fill=WHITE,
    )

    # Date and page number share the line below the edition box.
    date_text = _format_date(
        _edition_date(edition)
    )

    draw.text(
        (
            edition_left,
            190,
        ),
        date_text,
        font=_font(15, bold=True),
        fill=BLACK,
    )

    page_text = f"PAGE {page_number:02d}"

    page_bbox = draw.textbbox(
        (0, 0),
        page_text,
        font=_font(15, bold=True),
    )

    draw.text(
        (
            WIDTH - MARGIN - (page_bbox[2] - page_bbox[0]),
            190,
        ),
        page_text,
        font=_font(15, bold=True),
        fill=RED,
    )

    # Header line.
    y = 255

    draw.line(
        (MARGIN, y, WIDTH - MARGIN, y),
        fill=BLACK,
        width=5,
    )

    # ================================================================
    # CATEGORY BAR
    # ================================================================

    y += 13

    categories = [
        "WORLD",
        "BUSINESS",
        "TECHNOLOGY",
        "ECONOMY",
        "SCIENCE",
        "HEALTH",
        "SPORTS",
    ]

    cell_width = CONTENT_WIDTH / len(
        categories
    )

    for index, category in enumerate(
        categories
    ):
        cell_left = (
            MARGIN
            + index * cell_width
        )

        bbox = draw.textbbox(
            (0, 0),
            category,
            font=_font(16, bold=True),
        )

        draw.text(
            (
                cell_left
                + (
                    cell_width
                    - (bbox[2] - bbox[0])
                ) / 2,
                y,
            ),
            category,
            font=_font(16, bold=True),
            fill=BLACK,
        )

        if index < len(categories) - 1:
            x = (
                MARGIN
                + (index + 1) * cell_width
            )

            draw.line(
                (
                    x,
                    y - 2,
                    x,
                    y + 25,
                ),
                fill=RED,
                width=2,
            )

    y += 43

    draw.line(
        (MARGIN, y, WIDTH - MARGIN, y),
        fill=BLACK,
        width=2,
    )

    y += 15

    # ================================================================
    # EVENTS
    # ================================================================

    top = edition.get("top_story")

    if not isinstance(top, dict):
        top = None

    mains = [
        x for x in _list(
            edition.get("main_stories")
        )
        if isinstance(x, dict)
    ]

    briefs = [
        x for x in _list(
            edition.get("briefs")
        )
        if isinstance(x, dict)
    ]

    if top is None:
        combined = mains + briefs

        if combined:
            top = combined.pop(0)

    # ================================================================
    # TOP STORY AREA
    # ================================================================

    top_height = 590

    top_width = 930

    side_width = (
        CONTENT_WIDTH
        - top_width
        - 18
    )

    top_left = MARGIN
    top_right = top_left + top_width

    side_left = top_right + 18
    side_right = WIDTH - MARGIN

    if top:

        _paste(
            canvas,
            top,
            (
                top_left,
                y,
                top_right,
                y + top_height,
            ),
            "TOP STORY",
        )

        # Bottom black headline panel.
        panel_height = 215

        panel_top = (
            y
            + top_height
            - panel_height
        )

        draw.rectangle(
            (
                top_left,
                panel_top,
                top_right,
                y + top_height,
            ),
            fill=BLACK,
        )

        # Badge.
        draw.rectangle(
            (
                top_left,
                y,
                top_left + 145,
                y + 42,
            ),
            fill=RED,
        )

        draw.text(
            (
                top_left + 12,
                y + 8,
            ),
            "TOP STORY",
            font=_font(18, bold=True),
            fill=WHITE,
        )

        headline_y = panel_top + 18

        headline_y = _draw_block(
            draw,
            _title(top),
            top_left + 20,
            headline_y,
            _font(38, bold=True),
            WHITE,
            top_width - 40,
            max_lines=3,
            spacing=4,
        )

        _draw_block(
            draw,
            _summary(top),
            top_left + 20,
            headline_y + 5,
            _font(18),
            WHITE,
            top_width - 40,
            max_lines=3,
            spacing=4,
        )

    # ================================================================
    # BRIEF NEWS
    # ================================================================

    draw.rectangle(
        (
            side_left,
            y,
            side_right,
            y + 42,
        ),
        fill=BLACK,
    )

    bbox = draw.textbbox(
        (0, 0),
        "BRIEF NEWS",
        font=_font(19, bold=True),
    )

    draw.text(
        (
            side_left
            + (
                side_width
                - (bbox[2] - bbox[0])
            ) / 2,
            y + 8,
        ),
        "BRIEF NEWS",
        font=_font(19, bold=True),
        fill=WHITE,
    )

    brief_y = y + 53

    card_height = 122

    for event in briefs[:4]:

        image_width = 110

        _paste(
            canvas,
            event,
            (
                side_left,
                brief_y,
                side_left + image_width,
                brief_y + 105,
            ),
            "NEWS",
        )

        text_x = (
            side_left
            + image_width
            + 12
        )

        text_width = (
            side_width
            - image_width
            - 12
        )

        _draw_block(
            draw,
            _title(event),
            text_x,
            brief_y + 2,
            _font(16, bold=True),
            BLACK,
            text_width,
            max_lines=4,
            spacing=2,
        )

        draw.line(
            (
                side_left,
                brief_y + card_height - 5,
                side_right,
                brief_y + card_height - 5,
            ),
            fill=LIGHT_GRAY,
            width=1,
        )

        brief_y += card_height

    # ================================================================
    # LOWER GRID
    # ================================================================

    lower_y = (
        y
        + top_height
        + 18
    )

    draw.line(
        (
            MARGIN,
            lower_y,
            WIDTH - MARGIN,
            lower_y,
        ),
        fill=BLACK,
        width=3,
    )

    lower_y += 13

    left_width = 720
    right_left = MARGIN + left_width + 25
    right_width = (
        WIDTH
        - MARGIN
        - right_left
    )

    # ------------------------------------------------
    # MORE TOP NEWS
    # ------------------------------------------------

    draw.text(
        (MARGIN, lower_y),
        "MORE TOP NEWS",
        font=_font(21, bold=True),
        fill=BLACK,
    )

    draw.line(
        (
            MARGIN + 220,
            lower_y + 13,
            MARGIN + left_width,
            lower_y + 13,
        ),
        fill=RED,
        width=4,
    )

    news_y = lower_y + 40

    for event in mains[:3]:

        thumb_w = 175
        thumb_h = 100

        _paste(
            canvas,
            event,
            (
                MARGIN,
                news_y,
                MARGIN + thumb_w,
                news_y + thumb_h,
            ),
            "NEWS",
        )

        text_x = (
            MARGIN
            + thumb_w
            + 15
        )

        text_width = (
            left_width
            - thumb_w
            - 15
        )

        title_end = _draw_block(
            draw,
            _title(event),
            text_x,
            news_y,
            _font(18, bold=True),
            BLACK,
            text_width,
            max_lines=2,
            spacing=3,
        )

        _draw_block(
            draw,
            _summary(event),
            text_x,
            title_end + 3,
            _font(14),
            GRAY,
            text_width,
            max_lines=2,
            spacing=3,
        )

        news_y += 118

    # ------------------------------------------------
    # LATEST DEVELOPMENTS
    # ------------------------------------------------

    shown_ids = {
        id(event)
        for event in (
            [top] + mains + briefs
            if isinstance(top, dict)
            else mains + briefs
        )
        if isinstance(event, dict)
    }

    additional_events = []

    for key in (
        "additional_events",
        "remaining_events",
        "overflow_events",
    ):
        for event in _list(edition.get(key)):
            if not isinstance(event, dict):
                continue

            if id(event) in shown_ids:
                continue

            if any(
                id(existing) == id(event)
                for existing in additional_events
            ):
                continue

            additional_events.append(event)

    latest_events = additional_events[:2]

    if latest_events:

        # Keep LATEST DEVELOPMENTS beside MORE TOP NEWS.
        latest_top = lower_y

        latest_left = right_left
        latest_width = right_width

        draw.text(
            (
                latest_left,
                latest_top,
            ),
            "LATEST DEVELOPMENTS",
            font=_font(19, bold=True),
            fill=BLACK,
        )

        draw.line(
            (
                latest_left + 255,
                latest_top + 12,
                latest_left + latest_width,
                latest_top + 12,
            ),
            fill=RED,
            width=4,
        )

        latest_y = latest_top + 38

        for event in latest_events:

            latest_thumb_w = 150
            latest_thumb_h = 92

            _paste(
                canvas,
                event,
                (
                    latest_left,
                    latest_y,
                    latest_left + latest_thumb_w,
                    latest_y + latest_thumb_h,
                ),
                "NEWS",
            )

            latest_text_x = (
                latest_left
                + latest_thumb_w
                + 15
            )

            latest_text_width = (
                latest_width
                - latest_thumb_w
                - 15
            )

            latest_end = _draw_block(
                draw,
                _title(event),
                latest_text_x,
                latest_y,
                _font(17, bold=True),
                BLACK,
                latest_text_width,
                max_lines=2,
                spacing=3,
            )

            _draw_block(
                draw,
                _summary(event),
                latest_text_x,
                latest_end + 3,
                _font(12),
                GRAY,
                latest_text_width,
                max_lines=3,
                spacing=2,
            )

            latest_y += 112

    # ================================================================
    # FOOTER
    # ================================================================

    # Compact footer: social channels + Daily Brief + Support.
    footer_top = HEIGHT - 295

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

    # ---------------------------------------------------------------
    # FOLLOW US
    # ---------------------------------------------------------------

    follow_left = MARGIN
    follow_top = footer_top + 14

    draw.text(
        (follow_left, follow_top),
        "FOLLOW US",
        font=_font(15, bold=True),
        fill=BLACK,
    )

    # All channels on one line to preserve newspaper space.
    channels_y = footer_top + 46

    draw.text(
        (follow_left, channels_y),
        "Telegram",
        font=_font(14, bold=True),
        fill=BLACK,
    )

    # Headphone icon only for Telegram.
    draw.text(
        (follow_left + 72, channels_y - 1),
        "🎧",
        font=_font(13, bold=True),
        fill=RED,
    )

    draw.text(
        (follow_left + 91, channels_y),
        TELEGRAM_HANDLE,
        font=_font(14),
        fill=BLACK,
    )

    draw.text(
        (follow_left + 300, channels_y),
        "|",
        font=_font(14),
        fill=GRAY,
    )

    draw.text(
        (follow_left + 320, channels_y),
        "X",
        font=_font(14, bold=True),
        fill=BLACK,
    )

    draw.text(
        (follow_left + 345, channels_y),
        X_HANDLE,
        font=_font(14),
        fill=BLACK,
    )

    draw.text(
        (follow_left + 555, channels_y),
        "|",
        font=_font(14),
        fill=GRAY,
    )

    draw.text(
        (follow_left + 575, channels_y),
        "Instagram",
        font=_font(14, bold=True),
        fill=BLACK,
    )

    draw.text(
        (follow_left + 650, channels_y),
        INSTAGRAM_HANDLE,
        font=_font(14),
        fill=BLACK,
    )

    # ---------------------------------------------------------------
    # DAILY BRIEF
    # ---------------------------------------------------------------

    daily_left = MARGIN
    daily_top = footer_top + 86

    draw.text(
        (daily_left, daily_top),
        "DAILY BRIEF",
        font=_font(16, bold=True),
        fill=RED,
    )

    draw.text(
        (daily_left, daily_top + 27),
        "The most important stories, delivered in brief.",
        font=_font(12),
        fill=BLACK,
    )

    draw.text(
        (daily_left, daily_top + 49),
        "Three times daily",
        font=_font(11, bold=True),
        fill=BLACK,
    )

    draw.text(
        (daily_left + 122, daily_top + 49),
        "7:00  |  13:00  |  20:00",
        font=_font(11),
        fill=GRAY,
    )

    # ---------------------------------------------------------------
    # SUPPORT US
    # ---------------------------------------------------------------

    support_right = WIDTH - MARGIN
    support_left = 1010
    support_top = footer_top + 12

    # Compact support area.
    draw.text(
        (support_left, support_top),
        "SUPPORT US",
        font=_font(15, bold=True),
        fill=BLACK,
    )

    # Small explanatory text stacked underneath.
    support_text_y = support_top + 31

    draw.text(
        (support_left, support_text_y),
        "Your support helps us",
        font=_font(10),
        fill=BLACK,
    )

    draw.text(
        (support_left, support_text_y + 15),
        "keep independent news",
        font=_font(10),
        fill=BLACK,
    )

    draw.text(
        (support_left, support_text_y + 30),
        "accessible worldwide.",
        font=_font(10),
        fill=BLACK,
    )

    # QR placeholder on the far right.
    qr_size = 92

    qr_left = (
        support_right
        - qr_size
    )

    qr_top = footer_top + 17

    draw.rectangle(
        (
            qr_left,
            qr_top,
            qr_left + qr_size,
            qr_top + qr_size,
        ),
        outline=BLACK,
        width=2,
    )

    draw.text(
        (
            qr_left + 28,
            qr_top + 31,
        ),
        "QR",
        font=_font(21, bold=True),
        fill=GRAY,
    )

    # ================================================================
    # LEGAL
    # ================================================================

    legal_y = HEIGHT - 57

    draw.text(
        (
            MARGIN,
            legal_y,
        ),
        COPYRIGHT,
        font=_font(11, bold=True),
        fill=GRAY,
    )

    draw.text(
        (
            MARGIN,
            legal_y + 17,
        ),
        LEGAL,
        font=_font(9),
        fill=GRAY,
    )

    # ================================================================
    # BOTTOM TAGLINE
    # ================================================================

    bar_top = HEIGHT - 25

    draw.rectangle(
        (
            0,
            bar_top,
            WIDTH,
            HEIGHT,
        ),
        fill=RED,
    )

    font = _font(
        15,
        bold=True,
    )

    bbox = draw.textbbox(
        (0, 0),
        TAGLINE,
        font=font,
    )

    draw.text(
        (
            (WIDTH - (bbox[2] - bbox[0])) / 2,
            bar_top + 3,
        ),
        TAGLINE,
        font=font,
        fill=WHITE,
    )

    # ================================================================
    # SAVE
    # ================================================================

    canvas.save(
        output,
        format="PNG",
        optimize=True,
    )

    return output


# =====================================================================
# SECTION PAGE RENDERER
# =====================================================================


def _page_attr(page, name, default=None):
    if isinstance(page, dict):
        return page.get(name, default)
    return getattr(page, name, default)


def _section_event_text(event, key, default=""):
    if not isinstance(event, dict):
        return default

    content = event.get("content")
    if isinstance(content, dict):
        value = content.get(key)
        if value:
            return _safe_text(value)

    value = event.get(key)
    if value:
        return _safe_text(value)

    return default


def _section_event_title(event):
    return (
        _section_event_text(event, "headline")
        or _section_event_text(event, "title")
        or "NEWS"
    )


def _section_event_summary(event):
    return (
        _section_event_text(event, "summary")
        or _section_event_text(event, "description")
    )


def _section_event_sources(event):
    if not isinstance(event, dict):
        return ""

    content = event.get("content")
    if isinstance(content, dict):
        sources = content.get("sources")
    else:
        sources = event.get("sources")

    if isinstance(sources, (list, tuple)):
        values = [
            _safe_text(item)
            for item in sources
            if _safe_text(item)
        ]
        return " · ".join(values[:3])

    return _safe_text(sources)


def _section_has_image(event):
    try:
        path = _image_path(event)
        return bool(path and Path(path).exists())
    except Exception:
        return False


def _draw_section_header(canvas, draw, edition, page_number, title):
    logo_size = 250

    if LOGO_PATH.exists():
        try:
            with Image.open(LOGO_PATH) as source:
                logo = ImageOps.contain(
                    source.convert("RGB"),
                    (logo_size, logo_size),
                    Image.Resampling.LANCZOS,
                )
                canvas.paste(
                    logo,
                    (MARGIN, 20),
                )
        except Exception:
            pass

    brand_x = 305

    draw.text(
        (brand_x, 35),
        "AROUND",
        font=_font(65, bold=True),
        fill=BLACK,
    )

    draw.text(
        (brand_x, 100),
        "THE MAIN",
        font=_font(65, bold=True),
        fill=RED,
    )

    draw.text(
        (brand_x, 172),
        GLOBAL_NEWS,
        font=_font(24, bold=True),
        fill=BLACK,
    )

    draw.line(
        (
            brand_x + 220,
            184,
            brand_x + 275,
            184,
        ),
        fill=RED,
        width=4,
    )

    draw.text(
        (brand_x + 292, 172),
        SUBTITLE,
        font=_font(18),
        fill=GRAY,
    )

    edition_left = WIDTH - MARGIN - 300
    edition_top = 22
    edition_right = WIDTH - MARGIN
    edition_bottom = 172

    draw.rectangle(
        (
            edition_left,
            edition_top,
            edition_right,
            edition_bottom,
        ),
        fill=BLACK,
    )

    draw.rectangle(
        (
            edition_left,
            edition_top,
            edition_right,
            edition_top + 43,
        ),
        fill=RED,
    )

    draw.text(
        (
            edition_left + 18,
            edition_top + 8,
        ),
        "EDITION",
        font=_font(20, bold=True),
        fill=WHITE,
    )

    draw.text(
        (
            edition_left + 72,
            edition_top + 57,
        ),
        _edition_label(edition).replace("EDITION ", ""),
        font=_font(43, bold=True),
        fill=WHITE,
    )

    draw.text(
        (
            edition_left,
            190,
        ),
        _format_date(
            _edition_date(edition)
        ),
        font=_font(15, bold=True),
        fill=BLACK,
    )

    draw.text(
        (
            edition_left + 232,
            190,
        ),
        f"PAGE {page_number:02d}",
        font=_font(15, bold=True),
        fill=RED,
    )

    y = 255

    draw.line(
        (
            MARGIN,
            y,
            WIDTH - MARGIN,
            y,
        ),
        fill=BLACK,
        width=5,
    )

    y += 13

    categories = [
        "WORLD",
        "BUSINESS",
        "TECHNOLOGY",
        "ECONOMY",
        "SCIENCE",
        "HEALTH",
        "SPORTS",
    ]

    cell_width = CONTENT_WIDTH / len(categories)

    for index, category in enumerate(categories):
        cell_left = MARGIN + index * cell_width

        bbox = draw.textbbox(
            (0, 0),
            category,
            font=_font(16, bold=True),
        )

        draw.text(
            (
                cell_left
                + (
                    cell_width
                    - (bbox[2] - bbox[0])
                ) / 2,
                y,
            ),
            category,
            font=_font(16, bold=True),
            fill=BLACK,
        )

        if index < len(categories) - 1:
            draw.line(
                (
                    int(cell_left + cell_width),
                    y - 3,
                    int(cell_left + cell_width),
                    y + 27,
                ),
                fill=RED,
                width=2,
            )

    draw.line(
        (
            MARGIN,
            y + 34,
            WIDTH - MARGIN,
            y + 34,
        ),
        fill=BLACK,
        width=2,
    )


def _draw_section_title(draw, title, y):
    title = _safe_text(title).upper()

    draw.text(
        (MARGIN, y),
        title,
        font=_font(28, bold=True),
        fill=BLACK,
    )

    bbox = draw.textbbox(
        (0, 0),
        title,
        font=_font(28, bold=True),
    )

    line_left = MARGIN + (bbox[2] - bbox[0]) + 22

    draw.line(
        (
            line_left,
            y + 16,
            WIDTH - MARGIN,
            y + 16,
        ),
        fill=RED,
        width=5,
    )

    return y + 58


def _draw_article(
    canvas,
    draw,
    event,
    x,
    y,
    width,
    height,
    number,
    *,
    lead=False,
    image_height=None,
):
    gap = 10

    draw.text(
        (x, y),
        f"{number:02d}",
        font=_font(13, bold=True),
        fill=RED,
    )

    cursor_y = y + 22

    if image_height and _section_has_image(event):
        image_box = (
            x,
            cursor_y,
            x + width,
            cursor_y + image_height,
        )

        try:
            _paste(
                canvas,
                event,
                image_box,
                "NEWS",
            )
        except Exception:
            pass

        cursor_y += image_height + 12

    title_font_size = 30 if lead else 23

    title_lines = _wrap(
        draw,
        _section_event_title(event),
        _font(title_font_size, bold=True),
        width,
    )

    max_title_lines = 4 if lead else 3
    title_lines = title_lines[:max_title_lines]

    for line in title_lines:
        draw.text(
            (x, cursor_y),
            line,
            font=_font(title_font_size, bold=True),
            fill=BLACK,
        )
        cursor_y += title_font_size + 2

    draw.line(
        (
            x,
            cursor_y + 4,
            min(
                x + 92,
                x + width,
            ),
            cursor_y + 4,
        ),
        fill=RED,
        width=3,
    )

    cursor_y += 14

    summary = _section_event_summary(event)

    if summary:
        summary_font_size = 15 if lead else 13

        summary_lines = _wrap(
            draw,
            summary,
            _font(summary_font_size),
            width,
        )

        max_summary_lines = 5 if lead else 3

        for line in summary_lines[:max_summary_lines]:
            draw.text(
                (x, cursor_y),
                line,
                font=_font(summary_font_size),
                fill=GRAY,
            )
            cursor_y += summary_font_size + 3

    sources = _section_event_sources(event)

    if sources and cursor_y < y + height - 24:
        source_text = f"SOURCE: {sources.upper()}"

        draw.text(
            (x, y + height - 22),
            source_text,
            font=_font(9, bold=True),
            fill=GRAY,
        )

    return cursor_y


def _draw_compact_article(
    canvas,
    draw,
    event,
    x,
    y,
    width,
    height,
    number,
):
    thumb_width = min(190, int(width * 0.30))
    text_x = x
    text_width = width

    if _section_has_image(event):
        try:
            _paste(
                canvas,
                event,
                (
                    x,
                    y,
                    x + thumb_width,
                    y + height,
                ),
                "NEWS",
            )
            text_x = x + thumb_width + 14
            text_width = width - thumb_width - 14
        except Exception:
            pass

    draw.text(
        (text_x, y),
        f"{number:02d}",
        font=_font(11, bold=True),
        fill=RED,
    )

    title_y = y + 18

    title_lines = _wrap(
        draw,
        _section_event_title(event),
        _font(19, bold=True),
        text_width,
    )

    for line in title_lines[:3]:
        draw.text(
            (text_x, title_y),
            line,
            font=_font(19, bold=True),
            fill=BLACK,
        )
        title_y += 21

    draw.line(
        (
            text_x,
            title_y + 2,
            min(text_x + 70, text_x + text_width),
            title_y + 2,
        ),
        fill=RED,
        width=2,
    )

    summary = _section_event_summary(event)

    if summary:
        title_y += 10

        summary_lines = _wrap(
            draw,
            summary,
            _font(11),
            text_width,
        )

        for line in summary_lines[:3]:
            draw.text(
                (text_x, title_y),
                line,
                font=_font(11),
                fill=GRAY,
            )
            title_y += 14


def _draw_section_footer(draw):
    footer_top = 1720

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
        (MARGIN, footer_top + 14),
        "FOLLOW US",
        font=_font(14, bold=True),
        fill=BLACK,
    )

    draw.text(
        (MARGIN, footer_top + 43),
        f"Telegram 🎧 {TELEGRAM_HANDLE}",
        font=_font(11, bold=True),
        fill=BLACK,
    )

    draw.text(
        (MARGIN + 300, footer_top + 43),
        f"X  {X_HANDLE}",
        font=_font(11),
        fill=BLACK,
    )

    draw.text(
        (MARGIN + 525, footer_top + 43),
        f"Instagram {INSTAGRAM_HANDLE}",
        font=_font(11),
        fill=BLACK,
    )

    draw.text(
        (MARGIN, footer_top + 82),
        "DAILY BRIEF",
        font=_font(14, bold=True),
        fill=RED,
    )

    draw.text(
        (MARGIN, footer_top + 108),
        "The most important stories, delivered in brief.",
        font=_font(10),
        fill=BLACK,
    )

    draw.text(
        (MARGIN, footer_top + 130),
        "Three times daily  ·  7:00 | 13:00 | 20:00",
        font=_font(9),
        fill=GRAY,
    )



def _v6_page_value(page, name, default=None):
    if isinstance(page, dict):
        return page.get(name, default)
    return getattr(page, name, default)


def _v6_text(event, key, default=""):
    if not isinstance(event, dict):
        return default

    content = event.get("content")

    if isinstance(content, dict):
        value = content.get(key)
        if value:
            return _safe_text(value)

    value = event.get(key)

    if value:
        return _safe_text(value)

    return default


def _v6_title(event):
    return (
        _v6_text(event, "headline")
        or _v6_text(event, "title")
        or "NEWS"
    )


def _v6_summary(event):
    return (
        _v6_text(event, "summary")
        or _v6_text(event, "description")
    )


def _v6_sources(event):
    if not isinstance(event, dict):
        return ""

    content = event.get("content")

    if isinstance(content, dict):
        sources = content.get("sources")
    else:
        sources = event.get("sources")

    if isinstance(sources, (list, tuple)):
        values = [
            _safe_text(value)
            for value in sources
            if _safe_text(value)
        ]
        return " · ".join(values[:2])

    return _safe_text(sources)


def _v6_has_image(event):
    try:
        path = _image_path(event)
        return bool(path and Path(path).exists())
    except Exception:
        return False


@dataclass(frozen=True)
class SectionGeometry:
    """Fixed page landmarks shared by planning and drawing section pages."""

    nav_bottom: int = 303
    heading_top: int = 363
    heading_bottom: int = 421
    content_top: int = 433
    content_bottom: int = 1680
    footer_top: int = 1720


@dataclass(frozen=True)
class NewsBlock:
    event: dict
    number: int
    x: int
    y: int
    width: int
    height: int
    lead: bool = False


@dataclass(frozen=True)
class PagePlan:
    """Measured rectangles for one physical section page."""

    title: str
    blocks: tuple[NewsBlock, ...]
    geometry: SectionGeometry = SectionGeometry()


SECTION_GEOMETRY = SectionGeometry()


def _line_height(draw, font, spacing):
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    return bbox[3] - bbox[1] + spacing


def _v6_category(event):
    return (
        _v6_text(event, "category")
        or _v6_text(event, "section")
        or _v6_text(event, "topic")
        or "NEWS"
    ).upper()


def measure_news_block(draw, event, width, *, lead=False):
    """Return the exact height needed by a story at ``width``.

    This deliberately uses the same wrapping and fonts as the planned-card
    renderer.  It measures only a real local image; placeholders never make a
    section page taller.
    """
    if width <= 0:
        raise ValueError("news block width must be positive")

    category_font = _font(12, bold=True)
    # Narrow newspaper columns need a more generous text scale than the old
    # two-column cards.  These are fixed editorial styles, not page-filling
    # spacers: every pixel is still measured from real text and image content.
    title_font = _font(34 if lead else 30, bold=True)
    summary_font = _font(16 if lead else 15)
    source_font = _font(10, bold=True)

    image_height = 0
    text_width = width
    if lead and _v6_has_image(event):
        image_height = min(300, max(190, int(width * 0.28)))
    elif not lead and _v6_has_image(event):
        thumbnail = min(145, int(width * 0.31))
        text_width = max(80, width - thumbnail - 12)
        image_height = 118

    height = _line_height(draw, category_font, 3) + 5
    if image_height and lead:
        height += image_height + 12

    title_lines = _wrap(draw, _v6_title(event), title_font, text_width)
    height += len(title_lines) * _line_height(draw, title_font, 3)
    height += 14  # rule and its breathing room

    summary = _v6_summary(event)
    if summary:
        summary_lines = _wrap(draw, summary, summary_font, text_width)
        height += len(summary_lines) * _line_height(draw, summary_font, 3)

    sources = _v6_sources(event)
    if sources:
        source_lines = _wrap(
            draw, f"SOURCE: {sources.upper()}", source_font, text_width
        )
        height += 7 + len(source_lines) * _line_height(draw, source_font, 2)

    height += 8
    return max(height, image_height + 8)


def plan_section_pages(page):
    """Paginate measured stories in a three-column newspaper flow.

    The first physical page may reserve a two-column lead.  Every other story
    is measured at its real column width and then placed in the shortest
    column that can contain it.  This produces a masonry-like reading flow
    without count-based templates or hidden vertical reservations.
    """
    title = _safe_text(_v6_page_value(page, "title", ""))
    events = [
        event for event in _v6_page_value(page, "events", [])
        if isinstance(event, dict)
    ]
    if not events:
        return [PagePlan(title=title, blocks=())]

    measure_canvas = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(measure_canvas)
    plans = []
    index = 0
    story_number = 1
    first_page = True
    geometry = SECTION_GEOMETRY
    gap = 18
    column_count = 3
    column_width = (CONTENT_WIDTH - gap * (column_count - 1)) // column_count
    column_x = [MARGIN + index * (column_width + gap) for index in range(column_count)]

    while index < len(events):
        blocks = []
        column_bottoms = [geometry.content_top] * column_count

        # The edition's first story earns a genuine, two-column lead when it
        # fits naturally.  The third column remains available for compact
        # stories immediately, avoiding a rigid empty rectangle beside it.
        if first_page:
            lead_width = column_width * 2 + gap
            lead_height = measure_news_block(
                draw, events[index], lead_width, lead=True
            )
            if lead_height <= geometry.content_bottom - geometry.content_top:
                blocks.append(NewsBlock(
                    events[index], story_number, MARGIN, geometry.content_top,
                    lead_width, lead_height, lead=True,
                ))
                lead_bottom = geometry.content_top + lead_height + gap
                column_bottoms[0] = lead_bottom
                column_bottoms[1] = lead_bottom
                index += 1
                story_number += 1
            first_page = False

        while index < len(events):
            event = events[index]
            height = measure_news_block(draw, event, column_width)
            # Prefer the least-filled column, but do not force a story into a
            # column that would cross the footer boundary.
            fitting_columns = [
                column for column in range(column_count)
                if column_bottoms[column] + height <= geometry.content_bottom
            ]
            if not fitting_columns:
                break
            column = min(fitting_columns, key=lambda item: column_bottoms[item])
            blocks.append(NewsBlock(
                event, story_number, column_x[column], column_bottoms[column],
                column_width, height,
            ))
            column_bottoms[column] += height + gap
            index += 1
            story_number += 1

        # A single unusually long story gets its own measured lead page.  We
        # never crop text or silently reserve a fixed-height card.
        if not blocks:
            height = measure_news_block(draw, events[index], CONTENT_WIDTH, lead=True)
            if height > geometry.content_bottom - geometry.content_top:
                raise ValueError("story is too tall for a section page without truncation")
            blocks.append(NewsBlock(
                events[index], story_number, MARGIN, geometry.content_top,
                CONTENT_WIDTH, height, lead=True,
            ))
            index += 1
            story_number += 1

        plans.append(PagePlan(title=title, blocks=tuple(blocks)))

    return plans


def _v6_header(canvas, draw, edition, page_number):
    logo_size = 250

    if LOGO_PATH.exists():
        try:
            with Image.open(LOGO_PATH) as source:
                logo = ImageOps.contain(
                    source.convert("RGB"),
                    (logo_size, logo_size),
                    Image.Resampling.LANCZOS,
                )

                canvas.paste(
                    logo,
                    (MARGIN, 20),
                )
        except Exception:
            pass

    brand_x = 305

    draw.text(
        (brand_x, 35),
        "AROUND",
        font=_font(65, bold=True),
        fill=BLACK,
    )

    draw.text(
        (brand_x, 100),
        "THE MAIN",
        font=_font(65, bold=True),
        fill=RED,
    )

    draw.text(
        (brand_x, 172),
        GLOBAL_NEWS,
        font=_font(24, bold=True),
        fill=BLACK,
    )

    draw.line(
        (
            brand_x + 220,
            184,
            brand_x + 275,
            184,
        ),
        fill=RED,
        width=4,
    )

    draw.text(
        (brand_x + 292, 172),
        SUBTITLE,
        font=_font(18),
        fill=GRAY,
    )

    edition_left = WIDTH - MARGIN - 300
    edition_top = 22
    edition_right = WIDTH - MARGIN
    edition_bottom = 172

    draw.rectangle(
        (
            edition_left,
            edition_top,
            edition_right,
            edition_bottom,
        ),
        fill=BLACK,
    )

    draw.rectangle(
        (
            edition_left,
            edition_top,
            edition_right,
            edition_top + 43,
        ),
        fill=RED,
    )

    draw.text(
        (
            edition_left + 18,
            edition_top + 8,
        ),
        "EDITION",
        font=_font(20, bold=True),
        fill=WHITE,
    )

    draw.text(
        (
            edition_left + 72,
            edition_top + 57,
        ),
        _edition_label(edition).replace(
            "EDITION ",
            "",
        ),
        font=_font(43, bold=True),
        fill=WHITE,
    )

    draw.text(
        (
            edition_left,
            190,
        ),
        _format_date(
            _edition_date(edition)
        ),
        font=_font(15, bold=True),
        fill=BLACK,
    )

    draw.text(
        (
            edition_left + 232,
            190,
        ),
        f"PAGE {page_number:02d}",
        font=_font(15, bold=True),
        fill=RED,
    )

    # Category navigation.
    nav_top = 255

    draw.line(
        (
            MARGIN,
            nav_top,
            WIDTH - MARGIN,
            nav_top,
        ),
        fill=BLACK,
        width=5,
    )

    categories = [
        "WORLD",
        "BUSINESS",
        "TECHNOLOGY",
        "ECONOMY",
        "SCIENCE",
        "HEALTH",
        "SPORTS",
    ]

    cell_width = CONTENT_WIDTH / len(categories)

    for index, category in enumerate(categories):
        cell_left = MARGIN + index * cell_width

        bbox = draw.textbbox(
            (0, 0),
            category,
            font=_font(16, bold=True),
        )

        draw.text(
            (
                cell_left
                + (
                    cell_width
                    - (bbox[2] - bbox[0])
                ) / 2,
                nav_top + 13,
            ),
            category,
            font=_font(16, bold=True),
            fill=BLACK,
        )

        if index < len(categories) - 1:
            draw.line(
                (
                    int(cell_left + cell_width),
                    nav_top + 10,
                    int(cell_left + cell_width),
                    nav_top + 40,
                ),
                fill=RED,
                width=2,
            )

    draw.line(
        (
            MARGIN,
            nav_top + 48,
            WIDTH - MARGIN,
            nav_top + 48,
        ),
        fill=BLACK,
        width=2,
    )


def _v6_section_heading(draw, title, y):
    title = _safe_text(title).upper()

    draw.text(
        (MARGIN, y),
        title,
        font=_font(27, bold=True),
        fill=BLACK,
    )

    bbox = draw.textbbox(
        (0, 0),
        title,
        font=_font(27, bold=True),
    )

    line_left = MARGIN + (bbox[2] - bbox[0]) + 24

    draw.line(
        (
            line_left,
            y + 15,
            WIDTH - MARGIN,
            y + 15,
        ),
        fill=RED,
        width=5,
    )

    return y + 58


def _v6_article(
    canvas,
    draw,
    event,
    x,
    y,
    width,
    height,
    number,
    *,
    lead=False,
    image_height=0,
):
    draw.text(
        (x, y),
        f"{number:02d}",
        font=_font(
            12 if not lead else 14,
            bold=True,
        ),
        fill=RED,
    )

    cursor = y + (21 if not lead else 24)

    if image_height > 0 and _v6_has_image(event):
        try:
            _paste(
                canvas,
                event,
                (
                    x,
                    cursor,
                    x + width,
                    cursor + image_height,
                ),
                "NEWS",
            )
        except Exception:
            pass

        cursor += image_height + 10

    title_size = 28 if lead else 20

    lines = _wrap(
        draw,
        _v6_title(event),
        _font(title_size, bold=True),
        width,
    )

    max_lines = 4 if lead else 3

    for line in lines[:max_lines]:
        draw.text(
            (x, cursor),
            line,
            font=_font(title_size, bold=True),
            fill=BLACK,
        )
        cursor += title_size + 2

    draw.line(
        (
            x,
            cursor + 3,
            min(x + (95 if lead else 72), x + width),
            cursor + 3,
        ),
        fill=RED,
        width=3 if lead else 2,
    )

    cursor += 13

    summary = _v6_summary(event)

    if summary:
        summary_size = 14 if lead else 11

        lines = _wrap(
            draw,
            summary,
            _font(summary_size),
            width,
        )

        max_lines = 5 if lead else 3

        for line in lines[:max_lines]:
            draw.text(
                (x, cursor),
                line,
                font=_font(summary_size),
                fill=GRAY,
            )
            cursor += summary_size + 3

    sources = _v6_sources(event)

    if sources:
        draw.text(
            (
                x,
                y + height - 18,
            ),
            f"SOURCE: {sources.upper()}",
            font=_font(8, bold=True),
            fill=GRAY,
        )


def _v6_compact(
    canvas,
    draw,
    event,
    x,
    y,
    width,
    height,
    number,
):
    image_width = 0

    if _v6_has_image(event):
        image_width = min(
            175,
            int(width * 0.34),
        )

        try:
            _paste(
                canvas,
                event,
                (
                    x,
                    y,
                    x + image_width,
                    y + height,
                ),
                "NEWS",
            )
        except Exception:
            image_width = 0

    text_x = (
        x + image_width + 12
        if image_width
        else x
    )

    text_width = (
        width - image_width - 12
        if image_width
        else width
    )

    draw.text(
        (text_x, y),
        f"{number:02d}",
        font=_font(10, bold=True),
        fill=RED,
    )

    cursor = y + 17

    title_lines = _wrap(
        draw,
        _v6_title(event),
        _font(17, bold=True),
        text_width,
    )

    for line in title_lines[:3]:
        draw.text(
            (text_x, cursor),
            line,
            font=_font(17, bold=True),
            fill=BLACK,
        )
        cursor += 19

    draw.line(
        (
            text_x,
            cursor + 2,
            min(
                text_x + 62,
                text_x + text_width,
            ),
            cursor + 2,
        ),
        fill=RED,
        width=2,
    )

    cursor += 10

    summary = _v6_summary(event)

    if summary:
        lines = _wrap(
            draw,
            summary,
            _font(10),
            text_width,
        )

        for line in lines[:3]:
            draw.text(
                (text_x, cursor),
                line,
                font=_font(10),
                fill=GRAY,
            )
            cursor += 13


def _v6_footer(draw):
    footer_top = 1720

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
        (MARGIN, footer_top + 14),
        "FOLLOW US",
        font=_font(14, bold=True),
        fill=BLACK,
    )

    draw.text(
        (MARGIN, footer_top + 43),
        f"Telegram 🎧 {TELEGRAM_HANDLE}",
        font=_font(11, bold=True),
        fill=BLACK,
    )

    draw.text(
        (MARGIN + 300, footer_top + 43),
        f"X  {X_HANDLE}",
        font=_font(11),
        fill=BLACK,
    )

    draw.text(
        (MARGIN + 525, footer_top + 43),
        f"Instagram {INSTAGRAM_HANDLE}",
        font=_font(11),
        fill=BLACK,
    )

    draw.text(
        (MARGIN, footer_top + 82),
        "DAILY BRIEF",
        font=_font(14, bold=True),
        fill=RED,
    )

    draw.text(
        (MARGIN, footer_top + 108),
        "The most important stories, delivered in brief.",
        font=_font(10),
        fill=BLACK,
    )

    draw.text(
        (MARGIN, footer_top + 130),
        "Three times daily  ·  7:00 | 13:00 | 20:00",
        font=_font(9),
        fill=GRAY,
    )


def _render_section_page_fixed_layout(
    edition,
    page,
    output_path,
):
    if not isinstance(edition, dict):
        raise ValueError("edition must be a dictionary")

    output = Path(output_path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    canvas = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        WHITE,
    )

    draw = ImageDraw.Draw(canvas)

    page_number = int(
        _v6_page_value(
            page,
            "page_number",
            2,
        )
        or 2
    )

    title = _safe_text(
        _v6_page_value(
            page,
            "title",
            "",
        )
    )

    events = _v6_page_value(
        page,
        "events",
        [],
    )

    if not isinstance(events, list):
        events = []

    events = [
        event
        for event in events
        if isinstance(event, dict)
    ]

    _v6_header(
        canvas,
        draw,
        edition,
        page_number,
    )

    # IMPORTANT:
    # Navigation ends at ~303px. Section title starts at 330px,
    # so it can never collide with the category bar.
    section_y = 330

    section_y = _v6_section_heading(
        draw,
        title,
        section_y,
    )

    content_top = section_y + 8
    content_bottom = 1660

    if not events:
        draw.text(
            (
                MARGIN,
                content_top + 40,
            ),
            "NO PUBLISHED STORIES",
            font=_font(22, bold=True),
            fill=GRAY,
        )

        _v6_footer(draw)
        canvas.save(output, quality=95)
        return output

    count = len(events)

    # ================================================================
    # 1 STORY
    # ================================================================

    if count == 1:
        _v6_article(
            canvas,
            draw,
            events[0],
            MARGIN,
            content_top,
            CONTENT_WIDTH,
            1260,
            1,
            lead=True,
            image_height=470 if _v6_has_image(events[0]) else 0,
        )

    # ================================================================
    # 2 STORIES
    # ================================================================

    elif count == 2:
        gap = 22
        left = int(CONTENT_WIDTH * 0.63)
        right = CONTENT_WIDTH - left - gap

        x1 = MARGIN
        x2 = MARGIN + left + gap

        draw.line(
            (
                x2 - 11,
                content_top,
                x2 - 11,
                content_bottom,
            ),
            fill=BLACK,
            width=1,
        )

        _v6_article(
            canvas,
            draw,
            events[0],
            x1,
            content_top,
            left,
            1250,
            1,
            lead=True,
            image_height=400 if _v6_has_image(events[0]) else 0,
        )

        _v6_article(
            canvas,
            draw,
            events[1],
            x2,
            content_top,
            right,
            1250,
            2,
            image_height=260 if _v6_has_image(events[1]) else 0,
        )

    # ================================================================
    # 3 STORIES
    # ================================================================

    elif count == 3:
        gap = 22
        left = int(CONTENT_WIDTH * 0.60)
        right = CONTENT_WIDTH - left - gap

        x1 = MARGIN
        x2 = MARGIN + left + gap

        draw.line(
            (
                x2 - 11,
                content_top,
                x2 - 11,
                content_bottom,
            ),
            fill=BLACK,
            width=1,
        )

        _v6_article(
            canvas,
            draw,
            events[0],
            x1,
            content_top,
            left,
            1250,
            1,
            lead=True,
            image_height=430 if _v6_has_image(events[0]) else 0,
        )

        _v6_compact(
            canvas,
            draw,
            events[1],
            x2,
            content_top,
            right,
            360,
            2,
        )

        draw.line(
            (
                x2,
                content_top + 390,
                WIDTH - MARGIN,
                content_top + 390,
            ),
            fill=LIGHT_GRAY,
            width=1,
        )

        _v6_compact(
            canvas,
            draw,
            events[2],
            x2,
            content_top + 420,
            right,
            360,
            3,
        )

    # ================================================================
    # 4 STORIES
    # ================================================================

    elif count == 4:
        gap = 20
        col = int((CONTENT_WIDTH - gap) / 2)

        x1 = MARGIN
        x2 = MARGIN + col + gap

        top_height = 570

        draw.line(
            (
                x2 - 10,
                content_top,
                x2 - 10,
                content_top + top_height,
            ),
            fill=BLACK,
            width=1,
        )

        _v6_article(
            canvas,
            draw,
            events[0],
            x1,
            content_top,
            col,
            top_height,
            1,
            lead=True,
            image_height=270 if _v6_has_image(events[0]) else 0,
        )

        _v6_article(
            canvas,
            draw,
            events[1],
            x2,
            content_top,
            col,
            top_height,
            2,
            lead=True,
            image_height=270 if _v6_has_image(events[1]) else 0,
        )

        lower = content_top + top_height + 35

        draw.line(
            (
                MARGIN,
                lower - 15,
                WIDTH - MARGIN,
                lower - 15,
            ),
            fill=LIGHT_GRAY,
            width=1,
        )

        _v6_compact(
            canvas,
            draw,
            events[2],
            x1,
            lower,
            col,
            300,
            3,
        )

        _v6_compact(
            canvas,
            draw,
            events[3],
            x2,
            lower,
            col,
            300,
            4,
        )

    # ================================================================
    # 5+ STORIES
    #
    # Dense newspaper flow:
    #
    # ┌──────────────────────┬──────────────┐
    # │                      │ story        │
    # │     LEAD STORY       ├──────────────┤
    # │                      │ story        │
    # ├────────────┬────────┴──────────────┤
    # │ story      │ story      │ story     │
    # ├────────────┼────────────┼───────────┤
    # │ story      │ story      │ story     │
    # └────────────┴────────────┴───────────┘
    # ================================================================

    else:
        gap = 18
        left_width = int(CONTENT_WIDTH * 0.58)
        right_width = CONTENT_WIDTH - left_width - gap

        x_left = MARGIN
        x_right = MARGIN + left_width + gap

        lead_height = 540

        draw.line(
            (
                x_right - 9,
                content_top,
                x_right - 9,
                content_top + lead_height,
            ),
            fill=BLACK,
            width=1,
        )

        _v6_article(
            canvas,
            draw,
            events[0],
            x_left,
            content_top,
            left_width,
            lead_height,
            1,
            lead=True,
            image_height=260 if _v6_has_image(events[0]) else 0,
        )

        # Two stacked right-hand stories.
        side_height = 250

        _v6_compact(
            canvas,
            draw,
            events[1],
            x_right,
            content_top,
            right_width,
            side_height,
            2,
        )

        draw.line(
            (
                x_right,
                content_top + side_height + 15,
                WIDTH - MARGIN,
                content_top + side_height + 15,
            ),
            fill=LIGHT_GRAY,
            width=1,
        )

        if count > 2:
            _v6_compact(
                canvas,
                draw,
                events[2],
                x_right,
                content_top + side_height + 30,
                right_width,
                side_height,
                3,
            )

        # Remaining stories: 3-column newspaper grid.
        remaining = events[3:]

        if remaining:
            grid_top = content_top + lead_height + 35

            columns = 3
            grid_gap = 16
            grid_width = int(
                (
                    CONTENT_WIDTH
                    - grid_gap * (columns - 1)
                )
                / columns
            )

            row_height = 245

            for index, event in enumerate(
                remaining
            ):
                row = index // columns
                column = index % columns

                x = (
                    MARGIN
                    + column
                    * (grid_width + grid_gap)
                )

                y = (
                    grid_top
                    + row
                    * (row_height + 20)
                )

                if y > content_bottom - 180:
                    break

                if column > 0:
                    draw.line(
                        (
                            x - 8,
                            y,
                            x - 8,
                            y + row_height,
                        ),
                        fill=LIGHT_GRAY,
                        width=1,
                    )

                _v6_compact(
                    canvas,
                    draw,
                    event,
                    x,
                    y,
                    grid_width,
                    row_height,
                    index + 4,
                )

    _v6_footer(draw)

    canvas.save(
        output,
        quality=95,
    )

    return output


def _draw_planned_news_block(canvas, draw, block):
    """Draw one previously measured block without reserving hidden space."""
    event = block.event
    x, y, width = block.x, block.y, block.width
    lead = block.lead
    category_font = _font(12, bold=True)
    title_font = _font(34 if lead else 30, bold=True)
    summary_font = _font(16 if lead else 15)
    source_font = _font(10, bold=True)

    image_height = 0
    thumbnail = 0
    text_x = x
    text_width = width
    if lead and _v6_has_image(event):
        image_height = min(300, max(190, int(width * 0.28)))
    elif not lead and _v6_has_image(event):
        thumbnail = min(145, int(width * 0.31))
        image_height = 118
        text_x = x + thumbnail + 12
        text_width = width - thumbnail - 12
        _paste(canvas, event, (x, y, x + thumbnail, y + image_height), "NEWS")

    draw.text(
        (text_x, y),
        f"{block.number:02d}  {_v6_category(event)}",
        font=category_font,
        fill=RED,
    )
    cursor = y + _line_height(draw, category_font, 3) + 5

    if image_height and lead:
        _paste(canvas, event, (x, cursor, x + width, cursor + image_height), "NEWS")
        cursor += image_height + 12

    for line in _wrap(draw, _v6_title(event), title_font, text_width):
        draw.text((text_x, cursor), line, font=title_font, fill=BLACK)
        cursor += _line_height(draw, title_font, 3)

    draw.line(
        (text_x, cursor + 2, min(text_x + (95 if lead else 62), text_x + text_width), cursor + 2),
        fill=RED,
        width=3 if lead else 2,
    )
    cursor += 14

    summary = _v6_summary(event)
    if summary:
        for line in _wrap(draw, summary, summary_font, text_width):
            draw.text((text_x, cursor), line, font=summary_font, fill=GRAY)
            cursor += _line_height(draw, summary_font, 3)

    sources = _v6_sources(event)
    if sources:
        cursor += 7
        for line in _wrap(draw, f"SOURCE: {sources.upper()}", source_font, text_width):
            draw.text((text_x, cursor), line, font=source_font, fill=GRAY)
            cursor += _line_height(draw, source_font, 2)


def render_section_page(edition, page, output_path, *, page_number=None, page_plan=None):
    """Render a measured PagePlan for PAGE 02+; PAGE 01 remains untouched."""
    if not isinstance(edition, dict):
        raise ValueError("edition must be a dictionary")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(canvas)
    number = int(page_number or _v6_page_value(page, "page_number", 2) or 2)

    if page_plan is None:
        page_plan = plan_section_pages(page)[0]

    _v6_header(canvas, draw, edition, number)
    geometry = page_plan.geometry
    _v6_section_heading(draw, page_plan.title, geometry.heading_top)

    for block in page_plan.blocks:
        if block.y + block.height > geometry.content_bottom:
            raise ValueError("planned news block exceeds section content area")
        _draw_planned_news_block(canvas, draw, block)
        if not block.lead:
            draw.line(
                (block.x, block.y + block.height, block.x + block.width, block.y + block.height),
                fill=LIGHT_GRAY,
                width=1,
            )

    if not page_plan.blocks:
        draw.text(
            (MARGIN, geometry.content_top + 40),
            "NO PUBLISHED STORIES", font=_font(22, bold=True), fill=GRAY,
        )

    _v6_footer(draw)
    canvas.save(output, quality=95)
    return output
