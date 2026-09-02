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
PAGE_NUMBER = 1
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
    edition_left = WIDTH - MARGIN - 250
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
                250
                - (bbox[2] - bbox[0])
            ) / 2,
            edition_top + 53,
        ),
        number,
        font=_font(58, bold=True),
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
        font=_font(17, bold=True),
        fill=BLACK,
    )

    # Page number.
    draw.text(
        (
            WIDTH - MARGIN - 105,
            190,
        ),
        f"PAGE {PAGE_NUMBER:02d}",
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
    # IN FOCUS
    # ------------------------------------------------

    draw.text(
        (right_left, lower_y),
        "IN FOCUS",
        font=_font(21, bold=True),
        fill=BLACK,
    )

    draw.line(
        (
            right_left + 125,
            lower_y + 13,
            WIDTH - MARGIN,
            lower_y + 13,
        ),
        fill=RED,
        width=4,
    )

    focus_event = (
        briefs[4]
        if len(briefs) > 4
        else (
            mains[0]
            if mains
            else top
        )
    )

    focus_top = lower_y + 40
    focus_height = 230

    if focus_event:

        _paste(
            canvas,
            focus_event,
            (
                right_left,
                focus_top,
                WIDTH - MARGIN,
                focus_top + focus_height,
            ),
            "IN FOCUS",
        )

        focus_y = (
            focus_top
            + focus_height
            + 10
        )

        focus_y = _draw_block(
            draw,
            _title(focus_event),
            right_left,
            focus_y,
            _font(20, bold=True),
            BLACK,
            right_width,
            max_lines=2,
            spacing=3,
        )

        _draw_block(
            draw,
            _summary(focus_event),
            right_left,
            focus_y + 4,
            _font(14),
            GRAY,
            right_width,
            max_lines=3,
            spacing=3,
        )

    # ------------------------------------------------
    # CATEGORIES — positioned AFTER lower content
    # ------------------------------------------------

    category_top = max(
        news_y + 8,
        focus_top
        + focus_height
        + 145,
    )

    category_height = 290

    draw.rectangle(
        (
            right_left,
            category_top,
            WIDTH - MARGIN,
            category_top + category_height,
        ),
        outline=GRAY,
        width=2,
    )

    draw.rectangle(
        (
            right_left,
            category_top,
            WIDTH - MARGIN,
            category_top + 42,
        ),
        fill=RED,
    )

    draw.text(
        (
            right_left + 15,
            category_top + 8,
        ),
        "CATEGORIES",
        font=_font(19, bold=True),
        fill=WHITE,
    )

    category_y = category_top + 54

    for index, category in enumerate(
        categories
    ):

        draw.text(
            (
                right_left + 15,
                category_y,
            ),
            category,
            font=_font(14, bold=True),
            fill=BLACK,
        )

        number = f"{index + 2:02d}"

        bbox = draw.textbbox(
            (0, 0),
            number,
            font=_font(14, bold=True),
        )

        draw.text(
            (
                WIDTH
                - MARGIN
                - 15
                - (bbox[2] - bbox[0]),
                category_y,
            ),
            number,
            font=_font(14, bold=True),
            fill=RED,
        )

        category_y += 32

        if index < len(categories) - 1:
            draw.line(
                (
                    right_left + 10,
                    category_y - 7,
                    WIDTH - MARGIN - 10,
                    category_y - 7,
                ),
                fill=LIGHT_GRAY,
                width=1,
            )

    # ================================================================
    # FOOTER
    # ================================================================

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

    # Follow Us.
    follow_right = 700

    draw.rectangle(
        (
            MARGIN + 110,
            footer_top,
            follow_right,
            footer_top + 38,
        ),
        fill=BLACK,
    )

    draw.text(
        (
            MARGIN + 210,
            footer_top + 7,
        ),
        "FOLLOW US",
        font=_font(17, bold=True),
        fill=WHITE,
    )

    fy = footer_top + 53

    rows = [
        ("Telegram", TELEGRAM_HANDLE),
        ("X", X_HANDLE),
        ("Instagram", INSTAGRAM_HANDLE),
    ]

    for index, (name, handle) in enumerate(rows):

        row_y = fy + index * 31

        draw.text(
            (MARGIN, row_y),
            name,
            font=_font(16, bold=True),
            fill=BLACK,
        )

        draw.text(
            (MARGIN + 112, row_y),
            handle,
            font=_font(16),
            fill=BLACK,
        )

        if name == "Telegram":
            draw.text(
                (
                    MARGIN + 330,
                    row_y,
                ),
                "🎧 LISTEN",
                font=_font(14, bold=True),
                fill=RED,
            )

    # Support.
    support_left = 725
    support_right = WIDTH - MARGIN
    support_bottom = HEIGHT - 65

    draw.rectangle(
        (
            support_left,
            footer_top,
            support_right,
            support_bottom,
        ),
        outline=BLACK,
        width=2,
    )

    draw.text(
        (
            support_left + 16,
            footer_top + 13,
        ),
        "SUPPORT OUR INDEPENDENT JOURNALISM",
        font=_font(16, bold=True),
        fill=BLACK,
    )

    draw.text(
        (
            support_left + 16,
            footer_top + 44,
        ),
        "Your support helps us deliver unbiased,",
        font=_font(13),
        fill=BLACK,
    )

    draw.text(
        (
            support_left + 16,
            footer_top + 65,
        ),
        "accurate and timely news around the world.",
        font=_font(13),
        fill=BLACK,
    )

    # QR placeholder.
    qr_size = 115

    qr_left = (
        support_right
        - qr_size
        - 130
    )

    qr_top = footer_top + 45

    draw.rectangle(
        (
            qr_left,
            qr_top,
            qr_left + qr_size,
            qr_top + qr_size,
        ),
        outline=BLACK,
        width=3,
    )

    draw.text(
        (
            qr_left + 36,
            qr_top + 39,
        ),
        "QR",
        font=_font(24, bold=True),
        fill=GRAY,
    )

    draw.text(
        (
            support_right - 100,
            footer_top + 52,
        ),
        "SUPPORT",
        font=_font(17, bold=True),
        fill=RED,
    )

    draw.text(
        (
            support_right - 100,
            footer_top + 77,
        ),
        "NOW",
        font=_font(17, bold=True),
        fill=RED,
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
