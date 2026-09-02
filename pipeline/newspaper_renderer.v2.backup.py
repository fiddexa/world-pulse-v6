"""
AROUND THE MAIN - Newspaper Renderer

Converts an already-built edition into a smartphone-friendly
3:4 newspaper image.

This module:
- does not collect news;
- does not rank news;
- does not rewrite news;
- does not change editorial decisions;
- does not publish externally.

It only renders an existing edition visually.
"""

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------
# BRAND
# ---------------------------------------------------------------------

LOGO_PATH = Path("assets/logo.png")

BRAND_NAME = "AROUND THE MAIN"
TAGLINE = "STAY INFORMED. STAY AHEAD."
GLOBAL_NEWS = "GLOBAL NEWS"
SUBTITLE = "THE WORLD. THE MAIN. IN BRIEF."

TELEGRAM_HANDLE = "@aroundthemain"
X_HANDLE = "@aroundthemain"
INSTAGRAM_HANDLE = "@aroundthemain"

COPYRIGHT = "© 2026 AROUND THE MAIN. All rights reserved."
LEGAL = (
    "News independently prepared from cited sources. "
    "Third-party trademarks and materials belong to their respective owners."
)


# ---------------------------------------------------------------------
# FORMAT
# ---------------------------------------------------------------------

# 3:4 smartphone-oriented newspaper.
WIDTH = 1500
HEIGHT = 2000

MARGIN = 70
CONTENT_WIDTH = WIDTH - (MARGIN * 2)


# ---------------------------------------------------------------------
# COLORS
# ---------------------------------------------------------------------

BLACK = (12, 12, 12)
WHITE = (250, 250, 248)
RED = (190, 25, 35)
GRAY = (105, 105, 105)
LIGHT_GRAY = (220, 220, 216)
DARK_GRAY = (45, 45, 45)


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    import html

    return html.unescape(
        str(value)
    ).strip()


def _safe_list(value: Any) -> list:
    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return []


def _font(size: int, bold: bool = False):
    candidates = []

    if bold:
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ])
    else:
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ])

    for candidate in candidates:
        path = Path(candidate)

        if path.exists():
            return ImageFont.truetype(
                str(path),
                size,
            )

    return ImageFont.load_default()


def _content(event: Any) -> dict:
    if not isinstance(event, dict):
        return {}

    value = event.get("content")

    if isinstance(value, dict):
        return value

    return {}


def _publication(event: Any) -> dict:
    if not isinstance(event, dict):
        return {}

    value = event.get("publication")

    if isinstance(value, dict):
        return value

    return {}


def _event_title(event: dict) -> str:
    return _safe_text(
        _content(event).get("headline")
    )


def _event_summary(event: dict) -> str:
    content = _content(event)

    return _safe_text(
        content.get("summary")
        or content.get("body")
        or content.get("text")
    )


def _event_section(event: dict) -> str:
    value = _safe_text(
        _content(event).get("section")
    )

    return value.replace("_", " ").upper() or "WORLD"


def _event_sources(event: dict) -> str:
    publication = _publication(event)

    sources = publication.get("sources")

    if isinstance(sources, list):
        values = [
            _safe_text(item)
            for item in sources
            if _safe_text(item)
        ]

        if values:
            return "Sources: " + " | ".join(values)

    # Existing publication text may contain source information.
    telegram = _safe_text(
        publication.get("telegram")
    )

    for line in telegram.splitlines():
        if line.lower().startswith("sources:"):
            return line.strip()

    return ""


def _event_role(event: dict) -> str:
    editorial = event.get("editorial")

    if isinstance(editorial, dict):
        role = _safe_text(
            editorial.get("role")
        )

        if role:
            return role.upper()

    return "BRIEF"


def _edition_events(edition: dict) -> list:
    events = []

    top = edition.get("top_story")

    if isinstance(top, dict):
        events.append(top)

    for key in ("main_stories", "briefs"):
        for event in _safe_list(
            edition.get(key)
        ):
            if isinstance(event, dict):
                events.append(event)

    return events


def _edition_date(edition: dict) -> str:
    date = _safe_text(
        edition.get("edition_date")
    )

    if date:
        return date

    edition_id = _safe_text(
        edition.get("edition_id")
    )

    parts = edition_id.split("-")

    if len(parts) >= 7:
        return "-".join(parts[3:6])

    return ""


def _edition_time(edition: dict) -> str:
    return _safe_text(
        edition.get("edition_time")
    )


def _wrap_text(
    draw,
    text: str,
    font,
    max_width: int,
) -> list[str]:
    if not text:
        return []

    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = (
            word
            if not current
            else current + " " + word
        )

        box = draw.textbbox(
            (0, 0),
            candidate,
            font=font,
        )

        if box[2] - box[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return lines


def _draw_wrapped(
    draw,
    text,
    xy,
    font,
    fill,
    max_width,
    line_spacing=8,
    max_lines=None,
):
    lines = _wrap_text(
        draw,
        text,
        font,
        max_width,
    )

    if max_lines is not None:
        lines = lines[:max_lines]

    x, y = xy

    bbox = draw.textbbox(
        (x, y),
        "Ag",
        font=font,
    )

    line_height = (
        bbox[3] - bbox[1]
        + line_spacing
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


# ---------------------------------------------------------------------
# RENDERER
# ---------------------------------------------------------------------

def render_newspaper(
    edition: Any,
    output_path: str | Path,
) -> Path:
    """
    Render one edition into a 3:4 PNG newspaper.

    The edition itself is never modified.
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

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        WHITE,
    )

    draw = ImageDraw.Draw(image)

    # -------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------

    header_top = 45
    logo_size = 255

    # Official AROUND THE MAIN master logo.
    if LOGO_PATH.exists():
        with Image.open(LOGO_PATH) as logo:
            logo = logo.convert("RGB")
            logo.thumbnail(
                (logo_size, logo_size),
                Image.Resampling.LANCZOS,
            )

            logo_x = MARGIN
            logo_y = header_top

            image.paste(
                logo,
                (
                    logo_x,
                    logo_y,
                ),
            )

    # Brand name beside the logo.
    text_x = MARGIN + logo_size + 30
    text_y = header_top + 35

    draw.text(
        (text_x, text_y),
        BRAND_NAME,
        font=_font(57, bold=True),
        fill=BLACK,
    )

    draw.text(
        (text_x, text_y + 72),
        GLOBAL_NEWS,
        font=_font(24, bold=True),
        fill=RED,
    )

    draw.text(
        (text_x + 205, text_y + 72),
        SUBTITLE,
        font=_font(21),
        fill=DARK_GRAY,
    )

    # Edition box.
    edition_id = _safe_text(
        edition.get("edition_id")
    )

    date = _edition_date(edition)
    time = _edition_time(edition)

    box_width = 270
    box_left = WIDTH - MARGIN - box_width
    box_top = header_top + 5
    box_right = WIDTH - MARGIN
    box_bottom = header_top + 145

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
            box_top + 42,
        ),
        fill=RED,
    )

    draw.text(
        (box_left + 18, box_top + 7),
        "EDITION",
        font=_font(20, bold=True),
        fill=WHITE,
    )

    # Extract a readable edition number from the ID.
    edition_number = "001"

    if edition_id:
        # Keep the final numeric block where possible.
        parts = edition_id.split("-")

        for part in reversed(parts):
            if part.isdigit() and len(part) <= 4:
                edition_number = part
                break

    number_font = _font(48, bold=True)

    bbox = draw.textbbox(
        (0, 0),
        edition_number,
        font=number_font,
    )

    number_width = bbox[2] - bbox[0]

    draw.text(
        (
            box_left
            + (box_width - number_width) / 2,
            box_top + 50,
        ),
        edition_number,
        font=number_font,
        fill=WHITE,
    )

    # Publication date and time.
    meta_y = header_top + 165

    date_text = date

    if date:
        try:
            from datetime import datetime as _DateTime

            parsed_date = _DateTime.strptime(
                date,
                "%Y-%m-%d",
            )

            date_text = parsed_date.strftime(
                "%B %d, %Y"
            ).upper()

        except ValueError:
            pass

    if date_text:
        draw.text(
            (
                box_left,
                meta_y,
            ),
            date_text,
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
                box_right - (bbox[2] - bbox[0]),
                meta_y,
            ),
            time,
            font=_font(18, bold=True),
            fill=GRAY,
        )

    # Header separator.
    y = header_top + logo_size + 18

    draw.line(
        (MARGIN, y, WIDTH - MARGIN, y),
        fill=BLACK,
        width=4,
    )

    y += 20

    # Newspaper category bar.
    categories = [
        "WORLD",
        "GEOPOLITICS",
        "BUSINESS",
        "ECONOMY",
        "TECHNOLOGY",
        "SCIENCE",
        "HEALTH",
    ]

    category_font = _font(17, bold=True)

    available_width = CONTENT_WIDTH
    category_width = available_width / len(categories)

    for index, category in enumerate(categories):
        x = MARGIN + index * category_width

        bbox = draw.textbbox(
            (0, 0),
            category,
            font=category_font,
        )

        category_text_width = bbox[2] - bbox[0]

        draw.text(
            (
                x
                + (category_width - category_text_width) / 2,
                y,
            ),
            category,
            font=category_font,
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
                    y - 2,
                    separator_x,
                    y + 23,
                ),
                fill=RED,
                width=2,
            )

    y += 42

    draw.line(
        (MARGIN, y, WIDTH - MARGIN, y),
        fill=LIGHT_GRAY,
        width=2,
    )

    y += 22

    # -------------------------------------------------------------
    # TOP STORY
    # -------------------------------------------------------------

    top = edition.get("top_story")

    if isinstance(top, dict):
        draw.rectangle(
            (
                MARGIN,
                y,
                WIDTH - MARGIN,
                y + 12,
            ),
            fill=RED,
        )

        y += 28

        draw.text(
            (MARGIN, y),
            "TOP STORY",
            font=_font(27, bold=True),
            fill=RED,
        )

        y += 48

        title = _event_title(top)

        y = _draw_wrapped(
            draw,
            title,
            (MARGIN, y),
            _font(48, bold=True),
            BLACK,
            CONTENT_WIDTH,
            line_spacing=9,
            max_lines=4,
        )

        y += 18

        summary = _event_summary(top)

        y = _draw_wrapped(
            draw,
            summary,
            (MARGIN, y),
            _font(25),
            DARK_GRAY,
            CONTENT_WIDTH,
            line_spacing=9,
            max_lines=7,
        )

        source = _event_sources(top)

        if source:
            y += 14
            y = _draw_wrapped(
                draw,
                source,
                (MARGIN, y),
                _font(17),
                GRAY,
                CONTENT_WIDTH,
                line_spacing=5,
                max_lines=2,
            )

        y += 30

    # -------------------------------------------------------------
    # MAIN STORY
    # -------------------------------------------------------------

    main_stories = [
        event
        for event in _safe_list(
            edition.get("main_stories")
        )
        if isinstance(event, dict)
    ]

    if main_stories:
        draw.line(
            (MARGIN, y, WIDTH - MARGIN, y),
            fill=LIGHT_GRAY,
            width=2,
        )

        y += 22

        draw.text(
            (MARGIN, y),
            "MAIN",
            font=_font(25, bold=True),
            fill=RED,
        )

        y += 42

        for event in main_stories[:2]:
            title = _event_title(event)

            y = _draw_wrapped(
                draw,
                title,
                (MARGIN, y),
                _font(31, bold=True),
                BLACK,
                CONTENT_WIDTH,
                line_spacing=7,
                max_lines=3,
            )

            y += 8

            summary = _event_summary(event)

            y = _draw_wrapped(
                draw,
                summary,
                (MARGIN, y),
                _font(21),
                DARK_GRAY,
                CONTENT_WIDTH,
                line_spacing=7,
                max_lines=4,
            )

            source = _event_sources(event)

            if source:
                y += 8
                y = _draw_wrapped(
                    draw,
                    source,
                    (MARGIN, y),
                    _font(15),
                    GRAY,
                    CONTENT_WIDTH,
                    line_spacing=4,
                    max_lines=1,
                )

            y += 22

    # -------------------------------------------------------------
    # BRIEFS
    # -------------------------------------------------------------

    briefs = [
        event
        for event in _safe_list(
            edition.get("briefs")
        )
        if isinstance(event, dict)
    ]

    if briefs:
        draw.line(
            (MARGIN, y, WIDTH - MARGIN, y),
            fill=LIGHT_GRAY,
            width=2,
        )

        y += 22

        draw.text(
            (MARGIN, y),
            "BRIEFS",
            font=_font(25, bold=True),
            fill=RED,
        )

        y += 43

        for event in briefs:
            title = _event_title(event)

            y = _draw_wrapped(
                draw,
                title,
                (MARGIN, y),
                _font(23, bold=True),
                BLACK,
                CONTENT_WIDTH,
                line_spacing=5,
                max_lines=2,
            )

            y += 5

            summary = _event_summary(event)

            y = _draw_wrapped(
                draw,
                summary,
                (MARGIN, y),
                _font(18),
                DARK_GRAY,
                CONTENT_WIDTH,
                line_spacing=5,
                max_lines=3,
            )

            source = _event_sources(event)

            if source:
                y += 5
                y = _draw_wrapped(
                    draw,
                    source,
                    (MARGIN, y),
                    _font(13),
                    GRAY,
                    CONTENT_WIDTH,
                    line_spacing=3,
                    max_lines=1,
                )

            y += 16

            if y > HEIGHT - 430:
                break

    # -------------------------------------------------------------
    # FOOTER
    # -------------------------------------------------------------

    footer_top = HEIGHT - 370

    draw.line(
        (MARGIN, footer_top, WIDTH - MARGIN, footer_top),
        fill=BLACK,
        width=3,
    )

    footer_y = footer_top + 25

    draw.text(
        (MARGIN, footer_y),
        "FOLLOW US",
        font=_font(22, bold=True),
        fill=RED,
    )

    footer_y += 38

    draw.text(
        (MARGIN, footer_y),
        "Telegram",
        font=_font(19, bold=True),
        fill=BLACK,
    )

    draw.text(
        (MARGIN + 150, footer_y),
        TELEGRAM_HANDLE,
        font=_font(19),
        fill=DARK_GRAY,
    )

    # Small listening indicator beside Telegram.
    draw.text(
        (MARGIN + 390, footer_y - 2),
        "🎧 LISTEN",
        font=_font(18, bold=True),
        fill=RED,
    )

    footer_y += 32

    draw.text(
        (MARGIN, footer_y),
        "X",
        font=_font(19, bold=True),
        fill=BLACK,
    )

    draw.text(
        (MARGIN + 150, footer_y),
        X_HANDLE,
        font=_font(19),
        fill=DARK_GRAY,
    )

    footer_y += 32

    draw.text(
        (MARGIN, footer_y),
        "Instagram",
        font=_font(19, bold=True),
        fill=BLACK,
    )

    draw.text(
        (MARGIN + 150, footer_y),
        INSTAGRAM_HANDLE,
        font=_font(19),
        fill=DARK_GRAY,
    )

    footer_y += 43

    draw.text(
        (MARGIN, footer_y),
        "SUPPORT AROUND THE MAIN",
        font=_font(22, bold=True),
        fill=RED,
    )

    footer_y += 34

    draw.text(
        (MARGIN, footer_y),
        "Help us keep independent news coverage running.",
        font=_font(17),
        fill=DARK_GRAY,
    )

    footer_y += 39

    # QR placeholder.
    qr_left = WIDTH - MARGIN - 190
    qr_top = footer_top + 82
    qr_right = WIDTH - MARGIN
    qr_bottom = qr_top + 190

    draw.rectangle(
        (qr_left, qr_top, qr_right, qr_bottom),
        outline=BLACK,
        width=3,
    )

    draw.text(
        (
            qr_left + 47,
            qr_top + 78,
        ),
        "QR",
        font=_font(28, bold=True),
        fill=GRAY,
    )

    # -------------------------------------------------------------
    # LEGAL FOOTER
    # -------------------------------------------------------------

    legal_y = HEIGHT - 72

    draw.text(
        (MARGIN, legal_y),
        COPYRIGHT,
        font=_font(14, bold=True),
        fill=GRAY,
    )

    legal_y += 23

    _draw_wrapped(
        draw,
        LEGAL,
        (MARGIN, legal_y),
        _font(11),
        GRAY,
        CONTENT_WIDTH,
        line_spacing=2,
        max_lines=2,
    )

    # -------------------------------------------------------------
    # BRAND TAGLINE
    # -------------------------------------------------------------

    tagline_font = _font(17, bold=True)

    bbox = draw.textbbox(
        (0, 0),
        TAGLINE,
        font=tagline_font,
    )

    tagline_width = bbox[2] - bbox[0]

    draw.text(
        (
            WIDTH - MARGIN - tagline_width,
            HEIGHT - 25,
        ),
        TAGLINE,
        font=tagline_font,
        fill=RED,
    )

    image.save(
        output,
        format="PNG",
        optimize=True,
    )

    return output
