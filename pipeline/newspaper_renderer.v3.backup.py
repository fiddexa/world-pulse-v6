"""
AROUND THE MAIN - Newspaper Renderer V3

Visual newspaper layer for AROUND THE MAIN.

The renderer does NOT:
- collect news;
- rewrite news;
- rank news;
- make editorial decisions;
- publish externally.

It converts an already-built edition into a 3:4 newspaper image.

Image policy:
- only explicitly supplied local images are used;
- no automatic downloading from Reuters/AP/other news organizations;
- missing images receive a branded visual placeholder;
- a future licensed/AI image provider can be connected separately.
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
# FORMAT
# =====================================================================

WIDTH = 1500
HEIGHT = 2000

MARGIN = 35
CONTENT_WIDTH = WIDTH - MARGIN * 2

# =====================================================================
# COLORS
# =====================================================================

BLACK = (12, 12, 12)
WHITE = (250, 250, 248)
RED = (198, 20, 30)
DARK_RED = (145, 12, 20)
GRAY = (105, 105, 105)
MID_GRAY = (150, 150, 150)
LIGHT_GRAY = (218, 218, 214)
VERY_LIGHT = (242, 242, 239)

# =====================================================================
# FONTS
# =====================================================================


def _font(size: int, bold: bool = False):
    candidates = []

    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]

    for candidate in candidates:
        path = Path(candidate)

        if path.exists():
            return ImageFont.truetype(str(path), size)

    return ImageFont.load_default()


# =====================================================================
# TEXT HELPERS
# =====================================================================


def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    value = html.unescape(str(value))

    value = value.replace("\r", " ")
    value = value.replace("\n", " ")

    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _safe_list(value: Any) -> list:
    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return []


def _wrap(draw, text, font, width):
    text = _safe_text(text)

    if not text:
        return []

    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = word if not current else current + " " + word

        box = draw.textbbox(
            (0, 0),
            candidate,
            font=font,
        )

        if box[2] - box[0] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return lines


def _draw_text_block(
    draw,
    text,
    x,
    y,
    font,
    fill,
    width,
    max_lines=None,
    spacing=5,
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

    box = draw.textbbox(
        (0, 0),
        "Ag",
        font=font,
    )

    line_height = (
        box[3] - box[1]
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


# =====================================================================
# EDITION HELPERS
# =====================================================================


def _edition_events(edition):
    result = []

    top = edition.get("top_story")

    if isinstance(top, dict):
        result.append(("TOP", top))

    for event in _safe_list(
        edition.get("main_stories")
    ):
        if isinstance(event, dict):
            result.append(("MAIN", event))

    for event in _safe_list(
        edition.get("briefs")
    ):
        if isinstance(event, dict):
            result.append(("BRIEF", event))

    return result


def _content(event):
    value = event.get("content")

    return value if isinstance(value, dict) else {}


def _publication(event):
    value = event.get("publication")

    return value if isinstance(value, dict) else {}


def _title(event):
    content = _content(event)

    return _safe_text(
        content.get("headline")
        or event.get("headline")
        or event.get("title")
        or event.get("original_title")
    )


def _summary(event):
    content = _content(event)

    return _safe_text(
        content.get("summary")
        or content.get("body")
        or content.get("text")
        or event.get("summary")
    )


def _sources(event):
    publication = _publication(event)

    sources = publication.get("sources")

    if isinstance(sources, list):
        values = [
            _safe_text(item)
            for item in sources
            if _safe_text(item)
        ]

        if values:
            return _normalize_sources(values)

    telegram = _safe_text(
        publication.get("telegram")
    )

    for line in telegram.splitlines():
        if line.lower().startswith("sources:"):
            return _normalize_sources(
                line.split(":", 1)[1].split("|")
            )

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
        "bbc": "BBC",
    }

    result = []

    for value in values:
        clean = _safe_text(value)

        if not clean:
            continue

        key = clean.lower()

        result.append(
            mapping.get(key, clean)
        )

    # Preserve order while removing duplicates.
    result = list(dict.fromkeys(result))

    return (
        "Sources: "
        + " | ".join(result)
        if result
        else ""
    )


def _image_path(event):
    possible = [
        event.get("image_path"),
        event.get("image"),
        _content(event).get("image_path"),
        _content(event).get("image"),
    ]

    for value in possible:
        if not value:
            continue

        path = Path(str(value))

        if path.exists():
            return path

    return None


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

    return match.group(1) if match else ""


def _edition_time(edition):
    return _safe_text(
        edition.get("edition_time")
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


def _edition_number(edition):
    # Prefer an explicit number if future production supplies one.
    for key in (
        "edition_number",
        "issue_number",
        "issue",
    ):
        value = edition.get(key)

        if value is not None:
            text = _safe_text(value)

            if text:
                digits = re.sub(
                    r"\D",
                    "",
                    text,
                )

                if digits:
                    return digits.zfill(3)

    # V3 fallback.
    return "001"


# =====================================================================
# IMAGE HELPERS
# =====================================================================


def _placeholder(
    width,
    height,
    label,
    accent=RED,
):
    image = Image.new(
        "RGB",
        (width, height),
        BLACK,
    )

    draw = ImageDraw.Draw(image)

    # Abstract world-news visual.
    for radius in range(
        min(width, height) // 5,
        20,
        -18,
    ):
        bbox = (
            width // 2 - radius,
            height // 2 - radius,
            width // 2 + radius,
            height // 2 + radius,
        )

        draw.ellipse(
            bbox,
            outline=accent,
            width=2,
        )

    draw.line(
        (
            0,
            height,
            width,
            0,
        ),
        fill=accent,
        width=max(2, width // 180),
    )

    font = _font(
        max(20, min(width, height) // 12),
        bold=True,
    )

    label = _safe_text(label).upper()

    bbox = draw.textbbox(
        (0, 0),
        label,
        font=font,
    )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    draw.text(
        (
            (width - text_width) / 2,
            (height - text_height) / 2,
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


def _paste_image(
    canvas,
    event,
    box,
    label,
):
    left, top, right, bottom = box

    width = right - left
    height = bottom - top

    image = _load_image(
        event,
        width,
        height,
        label,
    )

    canvas.paste(
        image,
        (left, top),
    )


# =====================================================================
# BADGES
# =====================================================================


def _badge(draw, text, x, y, width):
    draw.rectangle(
        (
            x,
            y,
            x + width,
            y + 42,
        ),
        fill=RED,
    )

    draw.text(
        (
            x + 14,
            y + 7,
        ),
        text,
        font=_font(19, bold=True),
        fill=WHITE,
    )


# =====================================================================
# MAIN RENDERER
# =====================================================================


def render_newspaper(
    edition: Any,
    output_path: str | Path,
) -> Path:
    """
    Render one AROUND THE MAIN newspaper page.

    The edition dictionary is never modified.
    """

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

    # =================================================================
    # HEADER
    # =================================================================

    header_height = 300

    logo_box = (
        MARGIN,
        22,
        310,
        285,
    )

    if LOGO_PATH.exists():
        with Image.open(LOGO_PATH) as logo:
            logo = logo.convert("RGB")

            logo = ImageOps.contain(
                logo,
                (
                    logo_box[2] - logo_box[0],
                    logo_box[3] - logo_box[1],
                ),
                Image.Resampling.LANCZOS,
            )

            canvas.paste(
                logo,
                (
                    logo_box[0]
                    + (
                        logo_box[2]
                        - logo_box[0]
                        - logo.width
                    ) // 2,
                    logo_box[1]
                    + (
                        logo_box[3]
                        - logo_box[1]
                        - logo.height
                    ) // 2,
                ),
            )

    text_x = 335

    draw.text(
        (text_x, 43),
        "AROUND",
        font=_font(66, bold=True),
        fill=BLACK,
    )

    draw.text(
        (text_x, 110),
        "THE MAIN",
        font=_font(66, bold=True),
        fill=RED,
    )

    draw.text(
        (text_x, 181),
        GLOBAL_NEWS,
        font=_font(25, bold=True),
        fill=BLACK,
    )

    draw.line(
        (
            text_x + 215,
            193,
            text_x + 270,
            193,
        ),
        fill=RED,
        width=4,
    )

    draw.text(
        (text_x + 285, 181),
        SUBTITLE,
        font=_font(19),
        fill=DARK_GRAY if False else GRAY,
    )

    # Edition box.
    box_width = 250
    box_left = WIDTH - MARGIN - box_width
    box_top = 25
    box_right = WIDTH - MARGIN
    box_bottom = 180

    draw.rectangle(
        (
            box_left,
            box_top,
            box_right,
            box_bottom,
        ),
        fill=BLACK,
    )

    draw.rectangle(
        (
            box_left,
            box_top,
            box_right,
            box_top + 45,
        ),
        fill=RED,
    )

    draw.text(
        (
            box_left + 20,
            box_top + 8,
        ),
        "EDITION",
        font=_font(21, bold=True),
        fill=WHITE,
    )

    number = _edition_number(edition)

    bbox = draw.textbbox(
        (0, 0),
        number,
        font=_font(62, bold=True),
    )

    draw.text(
        (
            box_left
            + (
                box_width
                - (bbox[2] - bbox[0])
            ) / 2,
            box_top + 53,
        ),
        number,
        font=_font(62, bold=True),
        fill=WHITE,
    )

    date = _format_date(
        _edition_date(edition)
    )

    time = _edition_time(edition)

    draw.text(
        (box_left, 196),
        date,
        font=_font(18, bold=True),
        fill=BLACK,
    )

    if time:
        bbox = draw.textbbox(
            (0, 0),
            time,
            font=_font(18, bold=True),
        )

        draw.text(
            (
                box_right
                - (bbox[2] - bbox[0]),
                196,
            ),
            time,
            font=_font(18, bold=True),
            fill=BLACK,
        )

    # Header divider.
    y = header_height

    draw.line(
        (MARGIN, y, WIDTH - MARGIN, y),
        fill=BLACK,
        width=5,
    )

    # =================================================================
    # CATEGORY BAR
    # =================================================================

    categories = [
        "WORLD",
        "BUSINESS",
        "TECHNOLOGY",
        "ECONOMY",
        "SCIENCE",
        "HEALTH",
        "SPORTS",
    ]

    y += 15

    category_width = CONTENT_WIDTH / len(categories)

    for index, category in enumerate(categories):
        x = (
            MARGIN
            + index * category_width
        )

        bbox = draw.textbbox(
            (0, 0),
            category,
            font=_font(17, bold=True),
        )

        text_width = bbox[2] - bbox[0]

        draw.text(
            (
                x
                + (category_width - text_width) / 2,
                y,
            ),
            category,
            font=_font(17, bold=True),
            fill=BLACK,
        )

        if index < len(categories) - 1:
            separator_x = (
                MARGIN
                + (index + 1) * category_width
            )

            draw.line(
                (
                    separator_x,
                    y - 1,
                    separator_x,
                    y + 27,
                ),
                fill=RED,
                width=2,
            )

    y += 45

    draw.line(
        (MARGIN, y, WIDTH - MARGIN, y),
        fill=BLACK,
        width=2,
    )

    y += 18

    # =================================================================
    # CONTENT GRID
    # =================================================================

    events = _edition_events(edition)

    top = None
    mains = []
    briefs = []

    for role, event in events:
        if role == "TOP":
            top = event
        elif role == "MAIN":
            mains.append(event)
        else:
            briefs.append(event)

    # If there is no explicit top story, use first event.
    if top is None and events:
        top = events[0][1]

    # -----------------------------------------------------------------
    # TOP STORY + BRIEF NEWS
    # -----------------------------------------------------------------

    top_width = 930
    gap = 20
    side_width = (
        CONTENT_WIDTH
        - top_width
        - gap
    )

    top_height = 630

    top_left = MARGIN
    top_right = top_left + top_width

    side_left = top_right + gap
    side_right = WIDTH - MARGIN

    # Top story image.
    if top:
        image_top = y

        image_bottom = (
            image_top + top_height
        )

        _paste_image(
            canvas,
            top,
            (
                top_left,
                image_top,
                top_right,
                image_bottom,
            ),
            "TOP STORY",
        )

        # Dark bottom panel.
        panel_height = 245

        draw.rectangle(
            (
                top_left,
                image_bottom - panel_height,
                top_right,
                image_bottom,
            ),
            fill=(0, 0, 0),
        )

        _badge(
            draw,
            "TOP STORY",
            top_left,
            image_top,
            145,
        )

        title_y = (
            image_bottom
            - panel_height
            + 28
        )

        title_y = _draw_text_block(
            draw,
            _title(top),
            top_left + 25,
            title_y,
            _font(43, bold=True),
            WHITE,
            top_width - 50,
            max_lines=3,
            spacing=6,
        )

        title_y += 7

        _draw_text_block(
            draw,
            _summary(top),
            top_left + 25,
            title_y,
            _font(20),
            WHITE,
            top_width - 50,
            max_lines=3,
            spacing=5,
        )

    # -----------------------------------------------------------------
    # BRIEF NEWS
    # -----------------------------------------------------------------

    draw.rectangle(
        (
            side_left,
            y,
            side_right,
            y + 45,
        ),
        fill=BLACK,
    )

    bbox = draw.textbbox(
        (0, 0),
        "BRIEF NEWS",
        font=_font(21, bold=True),
    )

    draw.text(
        (
            side_left
            + (
                side_width
                - (bbox[2] - bbox[0])
            ) / 2,
            y + 9,
        ),
        "BRIEF NEWS",
        font=_font(21, bold=True),
        fill=WHITE,
    )

    brief_y = y + 58

    brief_card_height = 128

    for index, event in enumerate(
        briefs[:4]
    ):
        image_width = 112
        image_height = 112

        _paste_image(
            canvas,
            event,
            (
                side_left,
                brief_y,
                side_left + image_width,
                brief_y + image_height,
            ),
            "NEWS",
        )

        text_x = (
            side_left
            + image_width
            + 13
        )

        text_width = (
            side_width
            - image_width
            - 13
        )

        _draw_text_block(
            draw,
            _title(event),
            text_x,
            brief_y + 3,
            _font(17, bold=True),
            BLACK,
            text_width,
            max_lines=4,
            spacing=3,
        )

        source = _sources(event)

        if source:
            _draw_text_block(
                draw,
                source,
                text_x,
                brief_y + 91,
                _font(10),
                GRAY,
                text_width,
                max_lines=1,
                spacing=2,
            )

        draw.line(
            (
                side_left,
                brief_y + brief_card_height,
                side_right,
                brief_y + brief_card_height,
            ),
            fill=LIGHT_GRAY,
            width=2,
        )

        brief_y += brief_card_height + 9

    content_bottom = max(
        y + top_height,
        brief_y,
    )

    # =================================================================
    # LOWER CONTENT
    # =================================================================

    lower_y = content_bottom + 22

    draw.line(
        (MARGIN, lower_y, WIDTH - MARGIN, lower_y),
        fill=BLACK,
        width=3,
    )

    lower_y += 16

    # Left: MORE TOP NEWS
    left_width = 720

    draw.text(
        (MARGIN, lower_y),
        "MORE TOP NEWS",
        font=_font(22, bold=True),
        fill=BLACK,
    )

    draw.line(
        (
            MARGIN + 225,
            lower_y + 14,
            MARGIN + left_width,
            lower_y + 14,
        ),
        fill=RED,
        width=4,
    )

    news_y = lower_y + 43

    remaining = mains[:3]

    for event in remaining:
        thumb_w = 185
        thumb_h = 112

        _paste_image(
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

        text_x = MARGIN + thumb_w + 18
        text_width = left_width - thumb_w - 18

        news_y = _draw_text_block(
            draw,
            _title(event),
            text_x,
            news_y,
            _font(19, bold=True),
            BLACK,
            text_width,
            max_lines=3,
            spacing=4,
        )

        _draw_text_block(
            draw,
            _summary(event),
            text_x,
            news_y + 5,
            _font(15),
            GRAY,
            text_width,
            max_lines=2,
            spacing=3,
        )

        news_y += thumb_h + 13

    # -----------------------------------------------------------------
    # IN FOCUS
    # -----------------------------------------------------------------

    focus_left = MARGIN + left_width + 25
    focus_width = WIDTH - MARGIN - focus_left

    draw.text(
        (focus_left, lower_y),
        "IN FOCUS",
        font=_font(22, bold=True),
        fill=BLACK,
    )

    draw.line(
        (
            focus_left + 130,
            lower_y + 14,
            WIDTH - MARGIN,
            lower_y + 14,
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

    if focus_event:
        focus_image_top = lower_y + 43
        focus_image_bottom = (
            focus_image_top + 250
        )

        _paste_image(
            canvas,
            focus_event,
            (
                focus_left,
                focus_image_top,
                WIDTH - MARGIN,
                focus_image_bottom,
            ),
            "IN FOCUS",
        )

        focus_text_y = (
            focus_image_bottom + 12
        )

        focus_text_y = _draw_text_block(
            draw,
            _title(focus_event),
            focus_left,
            focus_text_y,
            _font(22, bold=True),
            BLACK,
            focus_width,
            max_lines=3,
            spacing=4,
        )

        _draw_text_block(
            draw,
            _summary(focus_event),
            focus_left,
            focus_text_y + 6,
            _font(16),
            GRAY,
            focus_width,
            max_lines=4,
            spacing=4,
        )

    # =================================================================
    # CATEGORIES
    # =================================================================

    category_box_top = lower_y + 365
    category_box_left = focus_left
    category_box_right = WIDTH - MARGIN
    category_box_bottom = category_box_top + 300

    draw.rectangle(
        (
            category_box_left,
            category_box_top,
            category_box_right,
            category_box_bottom,
        ),
        outline=GRAY,
        width=2,
    )

    draw.rectangle(
        (
            category_box_left,
            category_box_top,
            category_box_right,
            category_box_top + 43,
        ),
        fill=RED,
    )

    draw.text(
        (
            category_box_left + 18,
            category_box_top + 9,
        ),
        "CATEGORIES",
        font=_font(20, bold=True),
        fill=WHITE,
    )

    category_items = [
        "WORLD",
        "BUSINESS",
        "TECHNOLOGY",
        "ECONOMY",
        "SCIENCE",
        "HEALTH",
        "SPORTS",
    ]

    category_y = category_box_top + 57

    for index, category in enumerate(
        category_items
    ):
        draw.text(
            (
                category_box_left + 18,
                category_y,
            ),
            category,
            font=_font(15, bold=True),
            fill=BLACK,
        )

        draw.text(
            (
                category_box_right - 48,
                category_y,
            ),
            f"{index + 2:02d}",
            font=_font(15, bold=True),
            fill=RED,
        )

        category_y += 34

        if index < len(category_items) - 1:
            draw.line(
                (
                    category_box_left + 12,
                    category_y - 8,
                    category_box_right - 12,
                    category_y - 8,
                ),
                fill=LIGHT_GRAY,
                width=1,
            )

    # =================================================================
    # FOOTER
    # =================================================================

    footer_top = HEIGHT - 310

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
    follow_left = MARGIN
    follow_right = 720

    draw.rectangle(
        (
            follow_left + 115,
            footer_top - 1,
            follow_right - 40,
            footer_top + 39,
        ),
        fill=BLACK,
    )

    draw.text(
        (
            follow_left + 210,
            footer_top + 7,
        ),
        "FOLLOW US",
        font=_font(18, bold=True),
        fill=WHITE,
    )

    fy = footer_top + 54

    # Telegram.
    draw.text(
        (follow_left, fy),
        "Telegram",
        font=_font(17, bold=True),
        fill=BLACK,
    )

    draw.text(
        (follow_left + 115, fy),
        TELEGRAM_HANDLE,
        font=_font(17),
        fill=BLACK,
    )

    draw.text(
        (follow_left + 340, fy - 1),
        "🎧 LISTEN",
        font=_font(15, bold=True),
        fill=RED,
    )

    fy += 31

    draw.text(
        (follow_left, fy),
        "X",
        font=_font(17, bold=True),
        fill=BLACK,
    )

    draw.text(
        (follow_left + 115, fy),
        X_HANDLE,
        font=_font(17),
        fill=BLACK,
    )

    fy += 31

    draw.text(
        (follow_left, fy),
        "Instagram",
        font=_font(17, bold=True),
        fill=BLACK,
    )

    draw.text(
        (follow_left + 115, fy),
        INSTAGRAM_HANDLE,
        font=_font(17),
        fill=BLACK,
    )

    # Support box.
    support_left = 750
    support_right = WIDTH - MARGIN

    draw.rectangle(
        (
            support_left,
            footer_top,
            support_right,
            HEIGHT - 95,
        ),
        outline=BLACK,
        width=2,
    )

    draw.text(
        (
            support_left + 18,
            footer_top + 15,
        ),
        "SUPPORT OUR INDEPENDENT JOURNALISM",
        font=_font(17, bold=True),
        fill=BLACK,
    )

    draw.text(
        (
            support_left + 18,
            footer_top + 48,
        ),
        "Your support helps us deliver unbiased,",
        font=_font(14),
        fill=BLACK,
    )

    draw.text(
        (
            support_left + 18,
            footer_top + 70,
        ),
        "accurate and timely news around the world.",
        font=_font(14),
        fill=BLACK,
    )

    # QR placeholder.
    qr_size = 125

    qr_left = (
        support_right
        - qr_size
        - 135
    )

    qr_top = footer_top + 50

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
            qr_left + 38,
            qr_top + 45,
        ),
        "QR",
        font=_font(26, bold=True),
        fill=GRAY,
    )

    draw.text(
        (
            support_right - 105,
            footer_top + 57,
        ),
        "SUPPORT",
        font=_font(18, bold=True),
        fill=RED,
    )

    draw.text(
        (
            support_right - 105,
            footer_top + 82,
        ),
        "NOW",
        font=_font(18, bold=True),
        fill=RED,
    )

    # =================================================================
    # LEGAL + TAGLINE
    # =================================================================

    legal_y = HEIGHT - 82

    draw.text(
        (
            MARGIN,
            legal_y,
        ),
        COPYRIGHT,
        font=_font(12, bold=True),
        fill=GRAY,
    )

    draw.text(
        (
            MARGIN,
            legal_y + 21,
        ),
        LEGAL,
        font=_font(10),
        fill=GRAY,
    )

    # Red bottom bar.
    bar_top = HEIGHT - 35

    draw.rectangle(
        (
            0,
            bar_top,
            WIDTH,
            HEIGHT,
        ),
        fill=RED,
    )

    tagline_font = _font(
        18,
        bold=True,
    )

    bbox = draw.textbbox(
        (0, 0),
        TAGLINE,
        font=tagline_font,
    )

    tagline_width = (
        bbox[2] - bbox[0]
    )

    draw.text(
        (
            (WIDTH - tagline_width) / 2,
            bar_top + 5,
        ),
        TAGLINE,
        font=tagline_font,
        fill=WHITE,
    )

    # =================================================================
    # SAVE
    # =================================================================

    canvas.save(
        output,
        format="PNG",
        optimize=True,
    )

    return output
