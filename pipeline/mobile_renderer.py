from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from PIL import Image, ImageDraw, ImageFont, ImageOps
import qrcode
import hashlib
from urllib.parse import urlparse
from urllib.request import Request, urlopen


# =====================================================================
# BRAND / LAYOUT
# =====================================================================

BRAND_NAME = "AROUND THE MAIN"
TELEGRAM_HANDLE = "@aroundthemain"
X_HANDLE = "@aroundthemain"

RED = (190, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)
NEWSPAPER = (243, 233, 216)

WIDTH = 900
MARGIN = 36
CARD_GAP = 28

# Mobile Telegram page.
# Cards are never split between pages.
MOBILE_PAGE_HEIGHT = 1200

LOGO_PATH = Path("assets/logo.png")
X_LOGO_PATH = Path("assets/x/logo-black.png")


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

    content = event.get("content")

    if isinstance(content, dict):
        for key in (
            "headline",
            "title",
            "publication_title",
            "display_title",
        ):
            value = _safe_text(content.get(key))
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

    content = event.get("content")

    if isinstance(content, dict):
        for key in (
            "summary",
            "what_happened",
            "publication_summary",
            "description",
            "dek",
        ):
            value = _safe_text(content.get(key))
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
    def clean_sources(value) -> list[str]:
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

                if text and text not in result:
                    result.append(text)

            return result

        if isinstance(value, str) and value.strip():
            return [value.strip()]

        return []

    value = clean_sources(event.get("sources"))

    if value:
        return value

    content = event.get("content")

    if isinstance(content, dict):
        value = clean_sources(
            content.get("sources")
        )

        if value:
            return value

    verification = event.get("verification")

    if isinstance(verification, dict):
        value = clean_sources(
            verification.get("sources")
        )

        if value:
            return value

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

    content = event.get("content")

    image_url = event.get("image_url")

    if not image_url and isinstance(content, dict):
        image_url = content.get("image_url")

    if not image_url:
        for article in _list(event.get("articles")):
            if isinstance(article, dict):
                image_url = article.get("image_url")
                if image_url:
                    break

    if not image_url:
        return None

    image_url = _safe_text(image_url)

    try:
        parsed = urlparse(image_url)

        if parsed.scheme not in {"http", "https"}:
            return None

        hostname = (parsed.hostname or "").lower()

        # Only allow the trusted UN media host for automatic
        # production image caching.
        if not hostname.endswith("unitednations.entermediadb.net"):
            return None

        cache_dir = Path("data/images")
        cache_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        extension = ".jpg"

        path_name = Path(parsed.path).name.lower()

        for candidate in (".jpg", ".jpeg", ".png", ".webp"):
            if candidate in path_name:
                extension = candidate
                break

        digest = hashlib.sha256(
            image_url.encode("utf-8")
        ).hexdigest()[:20]

        local_path = cache_dir / f"{digest}{extension}"

        if local_path.exists() and local_path.stat().st_size > 0:
            return local_path

        request = Request(
            image_url,
            headers={
                "User-Agent": "AroundTheMain/1.0",
                "Accept": "image/avif,image/webp,image/jpeg,image/png,*/*",
            },
        )

        with urlopen(
            request,
            timeout=15,
        ) as response:
            data = response.read()

        if not data:
            return None

        local_path.write_bytes(data)

        # Validate that the downloaded file is a real image.
        with Image.open(local_path) as check:
            check.verify()

        return local_path

    except Exception:
        return None


def _has_real_image(event: dict) -> bool:
    return _image_path(event) is not None


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


def _edition_name(edition: dict) -> str:
    edition_time = _safe_text(
        edition.get("edition_time")
    )

    names = {
        "07:00": "MORNING BRIEFING",
        "13:00": "MIDDAY UPDATE",
        "20:00": "EVENING ROUND-UP",
    }

    return names.get(
        edition_time,
        "",
    )


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


def _event_card_label(event: dict) -> str:
    """Return a specific country/place/topic label for a news card."""

    if not isinstance(event, dict):
        return "WORLD"

    content = event.get("content")

    # Prefer explicit structured location/topic fields when available.
    containers = [event]
    if isinstance(content, dict):
        containers.append(content)

    keys = (
        "country",
        "countries",
        "location",
        "locations",
        "place",
        "region",
        "topic",
    )

    for container in containers:
        for key in keys:
            value = container.get(key)

            if isinstance(value, list):
                for item in value:
                    text = _safe_text(item)
                    if text:
                        return text.upper()[:24]

            else:
                text = _safe_text(value)
                if text:
                    return text.upper()[:24]

    # Fall back to recognizable locations in the headline.
    title = _safe_text(
        event.get("title")
        or event.get("headline")
        or (
            content.get("title")
            if isinstance(content, dict)
            else ""
        )
        or (
            content.get("headline")
            if isinstance(content, dict)
            else ""
        )
    )

    location_keywords = (
        "WEST BANK",
        "PALESTINE",
        "UKRAINE",
        "RUSSIA",
        "NEPAL",
        "ISRAEL",
        "IRAN",
        "IRAQ",
        "SYRIA",
        "LEBANON",
        "GAZA",
        "EUROPE",
        "CHINA",
        "INDIA",
        "PAKISTAN",
        "AFGHANISTAN",
        "UNITED STATES",
        "USA",
        "AMERICA",
        "NORTH KOREA",
        "SOUTH KOREA",
        "JAPAN",
        "TAIWAN",
        "TURKEY",
        "FRANCE",
        "GERMANY",
        "ITALY",
        "SPAIN",
        "BRITAIN",
        "UK",
        "AFRICA",
        "ASIA",
    )

    title_upper = title.upper()

    for keyword in location_keywords:
        if keyword in title_upper:
            return keyword

    # Existing section is the final fallback.
    return _event_category(event)


def _event_category(event: dict) -> str:
    """Return a concise location/topic label for the story card."""

    if not isinstance(event, dict):
        return "WORLD"

    # Prefer explicit location fields when available.
    location_keys = (
        "country",
        "country_name",
        "location",
        "place",
        "city",
        "region",
    )

    for key in location_keys:
        value = _safe_text(event.get(key))
        if value:
            return value.upper()[:24]

    # Some editions keep location metadata inside content.
    content = event.get("content")

    if isinstance(content, dict):
        for key in location_keys:
            value = _safe_text(content.get(key))
            if value:
                return value.upper()[:24]

    # Preserve the existing section-based fallback.
    if isinstance(content, dict):
        value = _safe_text(
            content.get("section")
        )

        if value:
            aliases = {
                "world": "WORLD",
                "geopolitics": "GEOPOLITICS",
                "business": "BUSINESS",
                "energy": "ENERGY",
                "technology": "TECHNOLOGY",
                "science_health": "SCIENCE & HEALTH",
                "climate": "CLIMATE",
                "trade_logistics": "TRADE & LOGISTICS",
                "society": "SOCIETY",
                "culture": "CULTURE",
                "sports": "SPORTS",
            }

            return aliases.get(
                value.strip().lower(),
                value.upper(),
            )

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


def _card_height(
    event: dict,
    *,
    compact: bool = False,
) -> int:
    """Calculate the rendered height of a split-layout news card."""

    if not isinstance(event, dict):
        return 180 if compact else 230

    probe = Image.new(
        "RGB",
        (WIDTH, MOBILE_PAGE_HEIGHT),
        NEWSPAPER,
    )
    probe_draw = ImageDraw.Draw(probe)

    # Card is split into text (left) and image (right).
    # Keep a comfortable text column while giving the image real visual weight.
    card_inner_width = WIDTH - MARGIN * 2 - 32
    image_width = 330
    text_width = card_inner_width - image_width - 24

    if compact:
        title_font = _font(20, bold=True)
        summary_font = _font(13)
        title_max_lines = 2
        summary_max_lines = 2
        min_height = 175
    else:
        title_font = _font(30, bold=True)
        summary_font = _font(18)
        title_max_lines = 5
        summary_max_lines = 5
        min_height = 320

    title_lines = _wrap(
        probe_draw,
        _title(event),
        title_font,
        text_width,
    )[:title_max_lines]

    title_line_height = (
        title_font.getbbox("Ag")[3]
        - title_font.getbbox("Ag")[1]
        + (4 if compact else 5)
    )

    summary = _summary(event)
    summary_lines = []

    if summary:
        summary_lines = _wrap(
            probe_draw,
            summary,
            summary_font,
            text_width,
        )[:summary_max_lines]

    summary_line_height = (
        summary_font.getbbox("Ag")[3]
        - summary_font.getbbox("Ag")[1]
        + (4 if compact else 5)
    )

    sources = _sources(event)
    source_lines = []

    if sources:
        source_text = "  •  ".join(sources[:3])
        source_lines = _wrap(
            probe_draw,
            source_text,
            _font(11),
            max(1, text_width - 55),
        )[:2]

    source_line_height = (
        _font(11).getbbox("Ag")[3]
        - _font(11).getbbox("Ag")[1]
        + 2
    )

    # Header band + vertical padding.
    height = 35 + 24

    if title_lines:
        height += len(title_lines) * title_line_height + (
            8 if compact else 12
        )

    if summary_lines:
        height += len(summary_lines) * summary_line_height + (
            7 if compact else 12
        )

    if source_lines:
        height += max(
            15 if compact else 18,
            len(source_lines) * source_line_height,
        ) + 7

    # The right-hand image needs enough height to look substantial.
    if _has_real_image(event):
        height = max(height, 35 + (155 if compact else 250) + 24)
    else:
        height = max(height, min_height)

    return max(min_height, min(430, height))

def render_mobile_edition(
    edition: dict,
    output_path: str | Path,
) -> Path:
    """
    Render one edition as a paginated mobile presentation.

    The edition remains one editorial unit.  Pages are only a visual
    presentation for mobile/Telegram.  A story is never split between
    pages.

    The first page is also written to the requested output_path for
    backward compatibility with the existing edition renderer.
    """

    if not isinstance(edition, dict):
        raise ValueError(
            "edition must be a dictionary"
        )

    output = Path(output_path)
    mobile_root = output.parent

    mobile_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    events = _collect_events(edition)

    header_height = 300
    footer_height = 250

    # PAGE 01: full branded header + edition information.
    # PAGES 02+: compact header.
    # Keep enough space for the full header, edition/date/page row,
    # and divider before the first story.
    content_top_first = header_height - 61
    content_top_other = MARGIN + 50

    content_bottom = (
    MOBILE_PAGE_HEIGHT
    - footer_height
    - MARGIN
    )

    available_first = content_bottom - content_top_first
    available_other = content_bottom - content_top_other

    # A page with no stories is still a valid mobile edition.
    pages: list[list[dict]] = []

    current_page: list[dict] = []
    current_height = 0

    for event_index, event in enumerate(events):
        # Story 01 is the lead story.
        # All following stories use compact cards.
        compact = event_index > 0

        event_height = _card_height(
            event,
            compact=compact,
        )

        required = event_height

        if current_page:
            required += CARD_GAP

        available = (
            available_first
            if not pages
            else available_other
        )

        # Keep the lead story large, then allow compact stories
        # to fill the remaining space on Page 01.
        if (
            current_page
            and current_height + required > available
        ):
            pages.append(current_page)
            current_page = []
            current_height = 0
            required = event_height
            available = available_other

        # On pages after the first, keep the existing compact-card
        # limit of two stories per page.
        if (
            pages
            and compact
            and len(current_page) >= 2
        ):
            pages.append(current_page)
            current_page = []
            current_height = 0
            required = event_height
            available = available_other

        current_page.append(event)
        current_height += required

    if current_page:
        pages.append(current_page)

    if not pages:
        pages = [[]]

    print("DEBUG PAGE DISTRIBUTION:")
    for i, page in enumerate(pages, 1):
        print(
            f"  PAGE {i}: "
            + ", ".join(
                f"{idx + 1}:{_title(event)[:40]}"
                for idx, event in enumerate(page)
            )
        )

    page_files: list[Path] = []

    def draw_header(
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        page_number: int,
    ) -> None:
        # =============================================================
        # PAGE 01 — FULL WIDTH BRANDED HEADER
        # =============================================================
        if page_number == 1:
            header_path = Path("assets/mobile-header.png")

            if header_path.exists():
                try:
                    with Image.open(header_path) as source:
                        header = source.convert("RGB")

                    # Exact mobile page width and compact header height.
                    header = ImageOps.fit(
                        header,
                        (
                            WIDTH,
                            235,
                        ),
                        method=Image.Resampling.LANCZOS,
                        centering=(0.5, 0.5),
                    )

                    canvas.paste(
                        header,
                        (0, 0),
                    )

                    # MORNING BRIEFING — placed in the open space
                    # between the interrupted top lines of the header.
                    briefing = "MORNING BRIEFING"

                    briefing_bbox = draw.textbbox(
                        (0, 0),
                        briefing,
                        font=_font(13, bold=True),
                    )

                    briefing_width = (
                        briefing_bbox[2] - briefing_bbox[0]
                    )

                    draw.text(
                        (
                            WIDTH - briefing_width - 109,
                            32,
                        ),
                        briefing,
                        font=_font(13, bold=True),
                        fill=BLACK,
                    )

                except Exception:
                    pass

            # ---------------------------------------------------------
            # EDITION / DATE / MORNING BRIEFING / PAGE
            # ---------------------------------------------------------

            info_y = 191

            edition_label = _edition_label(edition)
            edition_date = _format_date(
                _edition_date(edition)
            )
            edition_name = _edition_name(edition)

            draw.text(
                (
                    MARGIN,
                    info_y,
                ),
                edition_label,
                font=_font(13, bold=True),
                fill=RED,
            )

            # Divider after edition
            edition_width = draw.textbbox(
                (0, 0),
                edition_label,
                font=_font(13, bold=True),
            )[2]

            divider_1 = MARGIN + edition_width + 13

            draw.line(
                (
                    divider_1,
                    info_y + 1,
                    divider_1,
                    info_y + 15,
                ),
                fill=GRAY,
                width=1,
            )

            date_x = divider_1 + 14

            date_text = edition_date.upper()

            
            draw.text(
                (
                    date_x,
                    info_y,
                ),
                date_text,
                font=_font(13, bold=True),
                fill=BLACK,
            )

            page_text = f"PAGE {page_number:02d}"

            bbox = draw.textbbox(
                (0, 0),
                page_text,
                font=_font(13, bold=True),
            )

            draw.text(
                (
                    WIDTH
                    - MARGIN
                    - (bbox[2] - bbox[0]),
                    info_y,
                ),
                page_text,
                font=_font(13, bold=True),
                fill=BLACK,
            )

            # Divider under edition row
            draw.line(
                (
                    MARGIN,
                    info_y + 28,
                    WIDTH - MARGIN,
                    info_y + 28,
                ),
                fill=RED,
                width=1,
            )

        # =============================================================
        # PAGE 02+ — COMPACT TOP LINE ONLY
        # =============================================================
        else:
            info_y = MARGIN

            edition_label = _edition_label(edition)
            edition_date = _format_date(
                _edition_date(edition)
            )
            edition_name = _edition_name(edition)

            draw.text(
                (
                    MARGIN,
                    info_y,
                ),
                edition_label,
                font=_font(13, bold=True),
                fill=RED,
            )

            edition_width = draw.textbbox(
                (0, 0),
                edition_label,
                font=_font(13, bold=True),
            )[2]

            divider_1 = MARGIN + edition_width + 12

            draw.line(
                (
                    divider_1,
                    info_y + 1,
                    divider_1,
                    info_y + 20,
                ),
                fill=GRAY,
                width=2,
            )

            date_x = divider_1 + 14

            date_text = edition_date.upper()

            if edition_name:
                date_text += f"  •  {edition_name}"

            draw.text(
                (
                    date_x,
                    info_y,
                ),
                date_text,
                font=_font(13, bold=True),
                fill=BLACK,
            )

            page_text = f"PAGE {page_number:02d}"

            bbox = draw.textbbox(
                (0, 0),
                page_text,
                font=_font(13, bold=True),
            )

            draw.text(
                (
                    WIDTH
                    - MARGIN
                    - (bbox[2] - bbox[0]),
                    info_y,
                ),
                page_text,
                font=_font(13, bold=True),
                fill=BLACK,
            )

            draw.line(
                (
                    MARGIN,
                    info_y + 28,
                    WIDTH - MARGIN,
                    info_y + 28,
                ),
                fill=RED,
                width=1,
            )

    def draw_footer(
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        page_number: int,
    ) -> None:
        footer_path = Path("assets/footer.png")

        if not footer_path.exists():
            return

        try:
            with Image.open(footer_path) as source:
                footer = source.convert("RGB")

                
            # Fit the prepared footer to the full mobile page width.
            footer = ImageOps.fit(
                footer,
                (
                    WIDTH,
                    footer_height,
                ),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )

            footer_top = MOBILE_PAGE_HEIGHT - footer_height + 53

            # -------------------------------------------------------------
            # FOOTER
            # Page 1 = full footer
            # Pages 2+ = red bottom strip only
            # -------------------------------------------------------------

            if page_number == 1:

                canvas.paste(
                    footer,
                    (
                        0,
                        footer_top,
                    ),
                )

            else:

                # Red strip at the very bottom
                red_strip_height = 30

                draw.rectangle(
                    (
                         0,
                        MOBILE_PAGE_HEIGHT - red_strip_height,
                        WIDTH,
                        MOBILE_PAGE_HEIGHT,
                    ),
                    fill=RED,
                )

            # ---------------------------------------------------------
            # WORKING QR CODE — BUY ME A COFFEE
            # PAGE 1 ONLY
            # ---------------------------------------------------------
            if page_number == 1:

                qr = qrcode.make(
                    "https://buymeacoffee.com/aroundthemain"
                ).convert("RGB")

                qr_size = 133

                qr = qr.resize(
                    (qr_size, qr_size),
                    Image.Resampling.NEAREST,
                )

                qr_x = WIDTH - MARGIN - qr_size + 17
                qr_y = footer_top + 11

                canvas.paste(
                    qr,
                    (
                        qr_x,
                        qr_y,
                    ),
                )

        except Exception:
            pass


    def draw_markets_today(
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        y: int,
    ) -> None:
        """
        Compact MARKETS TODAY panel.
        Market snapshot for the test edition.
        """

        # -------------------------------------------------------------
        # MARKETS TODAY — TITLE
        # -------------------------------------------------------------
        draw.text(
            (MARGIN, y),
            "MARKETS TODAY",
            font=_font(13, bold=True),
            fill=RED,
        )

        # -------------------------------------------------------------
        # ROW 1 — INDEXES
        # -------------------------------------------------------------
        row1_y = y + 22

        draw.text(
            (MARGIN, row1_y),
            "INDEXES",
            font=_font(9, bold=True),
            fill=BLACK,
        )

        draw.text(
            (MARGIN + 52, row1_y),
            "S&P 500  7,747.71  +1.06%   |   NASDAQ  26,584.06  +1.40%   |   DOW  53,686.11  +1.18%",
            font=_font(8),
            fill=GRAY,
        )

        # -------------------------------------------------------------
        # ROW 2 — COMMODITIES
        # -------------------------------------------------------------
        row2_y = y + 40

        draw.text(
            (MARGIN, row2_y),
            "COMMODITIES",
            font=_font(9, bold=True),
            fill=BLACK,
        )

        draw.text(
            (MARGIN + 82, row2_y),
            "BRENT  $95.69  +0.46%   |   GOLD  $4,520.40  +0.96%   |   WTI  $91.71  +1.01%",
            font=_font(8),
            fill=GRAY,
        )

        # -------------------------------------------------------------
        # ROW 3 — CURRENCY / GLOBAL
        # -------------------------------------------------------------
        row3_y = y + 58

        draw.text(
            (MARGIN, row3_y),
            "CURRENCY / GLOBAL",
            font=_font(9, bold=True),
            fill=BLACK,
        )

        draw.text(
            (MARGIN + 108, row3_y),
            "EUR/USD  1.1627   |   DXY  99.12  +0.27%   |   USD/CNY  6.7113  -0.11%",
            font=_font(8),
            fill=GRAY,
        )

        # -------------------------------------------------------------
        # ROW 4 — MARKET LEADERS
        # -------------------------------------------------------------
        row4_y = y + 76

        draw.text(
            (MARGIN, row4_y),
            "MARKET LEADERS",
            font=_font(9, bold=True),
            fill=BLACK,
        )

        draw.text(
            (MARGIN + 91, row4_y),
            "NVIDIA  +1.80%   |   APPLE  +1.00%   |   TESLA  +5.42%",
            font=_font(8),
            fill=GRAY,
        )

    for page_number, page_events in enumerate(
        pages,
        start=1,
    ):
        page_path = (
            mobile_root
            / f"page-{page_number:02d}.png"
        )

        canvas = Image.new(
            "RGB",
            (
                WIDTH,
                MOBILE_PAGE_HEIGHT,
            ),
            NEWSPAPER,
        )

        draw = ImageDraw.Draw(canvas)

        draw_header(
            canvas,
            draw,
            page_number,
        )
        
        if page_number == 1:
            y = content_top_first
        else:
            y = content_top_other

        for index, event in enumerate(page_events):
            story_number = sum(
                len(previous_page)
                for previous_page in pages[: page_number - 1]
            ) + index + 1

            compact = story_number > 1

            card_height = _card_height(
                event,
                compact=compact,
            )

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

            category = _event_card_label(event)

            draw.rectangle(
                (
                    MARGIN,
                    card_top,
                    WIDTH - MARGIN,
                    card_top + 35,
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

            number_text = f"{story_number:02d}"

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

            text_x = MARGIN + 16
            text_width = WIDTH - MARGIN * 2 - 32

            has_image = _has_real_image(event)

            if compact:
                image_height = 155
                title_font = _font(20, bold=True)
                title_max_lines = 2
                title_spacing = 4
                summary_font = _font(13)
                summary_max_lines = 2
                summary_spacing = 4
                image_title_gap = 10
                title_summary_gap = 7
                image_top_offset = 50
                summary_source_gap = 7
            else:
                image_height = 180
                title_font = _font(30, bold=True)
                title_max_lines = 4
                title_spacing = 5
                summary_font = _font(18)
                summary_max_lines = 5
                summary_spacing = 5
                image_title_gap = 22
                title_summary_gap = 12
                image_top_offset = 58
                summary_source_gap = 15

            # ---------------------------------------------------------
            # SPLIT CARD — TEXT LEFT / IMAGE RIGHT
            # ---------------------------------------------------------

            card_inner_left = MARGIN + 16
            card_inner_right = WIDTH - MARGIN - 16
            card_inner_top = card_top + 50

            image_width = 330
            image_gap = 24

            image_left = (
                card_inner_right
                - image_width
            )

            text_x = card_inner_left
            text_width = (
                image_left
                - image_gap
                - text_x
            )

            if compact:
                image_height = min(
                    155,
                    card_height - 58,
                )
            else:
                image_height = min(
                    250,
                    card_height - 58,
                )

            if has_image:
                image = _load_image(
                    event,
                    image_width,
                    image_height,
                )

                canvas.paste(
                    image,
                    (
                        image_left,
                        card_inner_top,
                    ),
                )

            title_y = card_inner_top

            title_end = _draw_wrapped(
                draw,
                _title(event),
                text_x,
                title_y,
                title_font,
                BLACK,
                text_width,
                max_lines=title_max_lines,
                spacing=title_spacing,
            )

            current_y = title_end + title_summary_gap

            summary = _summary(event)

            if summary:
                summary_end = _draw_wrapped(
                    draw,
                    summary,
                    text_x,
                    current_y,
                    summary_font,
                    GRAY,
                    text_width,
                    max_lines=summary_max_lines,
                    spacing=summary_spacing,
                )

                current_y = summary_end + summary_source_gap

            sources = _sources(event)

            if sources:
                sources_y = current_y

                draw.text(
                    (
                        text_x,
                        sources_y,
                    ),
                    "SOURCE",
                    font=_font(11, bold=True),
                    fill=RED,
                )

                normalized_sources = []

                for source in sources[:3]:
                    value = _safe_text(source)

                    source_aliases = {
                        "un": "UN News",
                        "un news": "UN News",
                        "united nations": "United Nations",
                        "who": "WHO",
                        "unicef": "UNICEF",
                    }

                    value = source_aliases.get(
                        value.lower(),
                        value,
                    )

                    if value and value not in normalized_sources:
                        normalized_sources.append(value)

                source_text = "  •  ".join(
                    normalized_sources
                )

                _draw_wrapped(
                    draw,
                    source_text,
                    text_x + 55,
                    sources_y - 2,
                    _font(11),
                    GRAY,
                    text_width - 55,
                    max_lines=2,
                    spacing=2,
                )

            y = card_bottom + CARD_GAP

        # -------------------------------------------------------------
        # PAGE 01 — MARKETS TODAY + FULL FOOTER
        # -------------------------------------------------------------

        if page_number == 1:

            markets_y = MOBILE_PAGE_HEIGHT - footer_height - 43

            draw_markets_today(
                canvas,
                draw,
                markets_y,
            )

            draw_footer(
                canvas,
                draw,
                page_number,
            )

        # -------------------------------------------------------------
        # PAGES 2+ — ONLY BOTTOM RED STRIPE
        # -------------------------------------------------------------

        else:

            red_bar_height = 28

            draw.rectangle(
                (
                    0,
                    MOBILE_PAGE_HEIGHT - red_bar_height,
                    WIDTH,
                    MOBILE_PAGE_HEIGHT,
                ),
                fill=RED,
            )

            draw.text(
                (
                    WIDTH // 2,
                    MOBILE_PAGE_HEIGHT - red_bar_height // 2,
                ),
                "Global News  |  Minimum text  |  Maximum meaning",
                font=_font(11, bold=False),
                fill=WHITE,
                anchor="mm",
            )

        # -------------------------------------------------------------
        # SAVE PAGE
        # -------------------------------------------------------------

        canvas.save(
            page_path,
            format="PNG",
            optimize=True,
        )

        page_files.append(page_path)       

    # Keep the normal paginated files and also provide the
    # requested legacy mobile.png as a copy of PAGE 01.
    first_page = page_files[0]

    if output != first_page:
        if output.exists():
            output.unlink()

        first_page.replace(output)

        # Restore PAGE 01 so the paginated set remains complete.
        first_page.write_bytes(output.read_bytes())

    return output
