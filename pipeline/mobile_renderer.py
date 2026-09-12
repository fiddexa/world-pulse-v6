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
CARD_GAP = 21

# Mobile Telegram page.
# Cards are never split between pages.
MOBILE_PAGE_HEIGHT = 1200

LOGO_PATH = Path("assets/logo.png")
X_LOGO_PATH = Path("assets/x/logo-black.png")


# =====================================================================
# HELPERS
# =====================================================================

def _font(
    size: int,
    bold: bool = False,
    italic: bool = False,
) -> ImageFont.FreeTypeFont:
    if bold and italic:
        font_path = "/usr/share/fonts/opentype/inter/Inter-BoldItalic.otf"
    elif bold:
        font_path = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
    elif italic:
        font_path = "/usr/share/fonts/opentype/inter/Inter-Italic.otf"
    else:
        font_path = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"

    path = Path(font_path)

    if path.exists():
        return ImageFont.truetype(str(path), size)

    # Fallback if Inter is unavailable.
    if bold and italic:
        fallback = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
    elif bold:
        fallback = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    elif italic:
        fallback = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"
    else:
        fallback = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    fallback_path = Path(fallback)

    if fallback_path.exists():
        return ImageFont.truetype(str(fallback_path), size)

    return ImageFont.load_default()


# =====================================================================
# LAST PAGE BRANDING / INFORMATION
# =====================================================================

LAST_PAGE_LOGO = Path(
    "assets/around_the_main_last_page_3x1.png"
)

LAST_PAGE_FREE_SPACE_THRESHOLD = 0.25
LAST_PAGE_STANDARD_THRESHOLD = 0.40
LAST_PAGE_LARGE_THRESHOLD = 0.55
LAST_PAGE_BLOCK_GAP = 18
LAST_PAGE_FOOTER_GAP = 16

INFO_RIGHTS_POLICY = (
    "We gather information from publicly available and reputable news "
    "sources, then independently edit and summarize it for clarity, "
    "context and informational purposes. We respect intellectual "
    "property rights and do not claim ownership of third-party materials."
)

INFO_RIGHTS_POLICY_2 = (
    "Trademarks, logos, photographs and other protected materials remain "
    "the property of their respective owners and are used with attribution "
    "where applicable. No affiliation, endorsement or transfer of rights "
    "is implied."
)

PUBLICATION_NOTICE = (
    "AROUND THE MAIN is an independent editorial project. Content is "
    "provided for informational purposes and does not constitute "
    "professional, financial, legal or other advice."
)


def _last_page_info_metrics(draw, width: int) -> dict:
    """
    Measure the complete information block.

    The same text, font and spacing are used whether or not
    the last-page banner is present.
    """
    font = _font(11, italic=True)
    heading_font = _font(11, italic=True)

    heading = "INFORMATION & RIGHTS"

    heading_bbox = draw.textbbox(
        (0, 0),
        heading,
        font=heading_font,
    )

    heading_height = (
        heading_bbox[3] - heading_bbox[1]
    )

    paragraphs = [
        INFO_RIGHTS_POLICY,
        INFO_RIGHTS_POLICY_2,
        PUBLICATION_NOTICE,
    ]

    paragraph_lines = []

    for paragraph in paragraphs:
        lines = _wrap(
            draw,
            paragraph,
            font,
            width,
        )

        paragraph_lines.append(
            max(1, len(lines))
        )

    line_height = (
        font.getbbox("Ag")[3]
        - font.getbbox("Ag")[1]
    )

    # Compact italic block.
    heading_gap = 5
    paragraph_gap = 4
    top_padding = 7
    bottom_padding = 7

    text_height = sum(
        count * line_height
        + (count - 1)
        for count in paragraph_lines
    )

    gaps = (
        heading_gap
        + paragraph_gap * (len(paragraphs) - 1)
    )

    total_height = (
        top_padding
        + heading_height
        + gaps
        + text_height
        + bottom_padding
    )

    return {
        "height": total_height,
        "font": font,
        "heading_font": heading_font,
        "line_height": line_height,
        "heading": heading,
        "paragraphs": paragraphs,
        "heading_gap": heading_gap,
        "paragraph_gap": paragraph_gap,
        "top_padding": top_padding,
        "bottom_padding": bottom_padding,
    }


def _draw_last_page_info(
    canvas,
    draw,
    *,
    top: int,
    width: int,
) -> int | None:
    """
    Draw the complete information block without truncation.

    Returns the bottom coordinate when successful.
    """
    metrics = _last_page_info_metrics(
        draw,
        width,
    )

    cursor = top + metrics["top_padding"]

    draw.text(
        (MARGIN, cursor),
        metrics["heading"],
        font=metrics["heading_font"],
        fill=RED,
    )

    heading_bbox = draw.textbbox(
        (0, 0),
        metrics["heading"],
        font=metrics["heading_font"],
    )

    cursor += (
        heading_bbox[3]
        - heading_bbox[1]
        + metrics["heading_gap"]
    )

    for index, paragraph in enumerate(
        metrics["paragraphs"]
    ):
        cursor = _draw_wrapped(
            draw,
            paragraph,
            MARGIN,
            cursor,
            metrics["font"],
            GRAY if index < 2 else BLACK,
            width,
            max_lines=20,
            spacing=1,
        )

        if index < len(metrics["paragraphs"]) - 1:
            cursor += metrics["paragraph_gap"]

    cursor += metrics["bottom_padding"]

    return cursor


def _draw_last_page_branding(
    canvas,
    draw,
    *,
    last_content_bottom: int,
    available_bottom: int,
) -> dict:
    """
    Fill the final-page free area aesthetically.

    Rules:
    - >=55%: large banner + info
    - 40-55%: standard banner + info
    - 25-40%: compact banner + info
    - <25%: info only, if the complete info block fits
    - if complete info does not fit: nothing
    """
    free_height = max(
        0,
        available_bottom
        - last_content_bottom
        - LAST_PAGE_BLOCK_GAP,
    )

    if free_height <= 0:
        return {
            "drawn": False,
            "variant": "NONE",
            "free_height": free_height,
        }

    content_width = (
        WIDTH
        - MARGIN * 2
    )

    info_metrics = _last_page_info_metrics(
        draw,
        content_width,
    )

    info_height = info_metrics["height"]

    # The information block is the absolute minimum.
    if free_height < info_height:
        return {
            "drawn": False,
            "variant": "NONE",
            "free_height": free_height,
            "info_height": info_height,
        }

    free_ratio = (
        free_height
        / MOBILE_PAGE_HEIGHT
    )

    variant = "INFO_ONLY"
    logo_width = 0
    banner_height = 0

    if free_ratio >= LAST_PAGE_LARGE_THRESHOLD:
        variant = "LARGE"
        logo_width = 720
        banner_height = 240

    elif free_ratio >= LAST_PAGE_STANDARD_THRESHOLD:
        variant = "STANDARD"
        logo_width = 560
        banner_height = 187

    elif free_ratio >= LAST_PAGE_FREE_SPACE_THRESHOLD:
        variant = "COMPACT"
        logo_width = 420
        banner_height = 140

    # Check whether the chosen banner + info actually fit.
    if variant != "INFO_ONLY":
        logo_width = min(
            logo_width,
            content_width,
        )

        try:
            with Image.open(
                LAST_PAGE_LOGO
            ) as source:
                logo = source.convert("RGBA")

            logo_height = int(
                logo.height
                * logo_width
                / logo.width
            )

            logo_height = min(
                logo_height,
                banner_height,
            )

            required = (
                logo_height
                + LAST_PAGE_BLOCK_GAP
                + info_height
            )

            if required > free_height:
                # Try the next smaller banner.
                if variant == "LARGE":
                    variant = "STANDARD"
                    logo_width = 560
                    banner_height = 187

                elif variant == "STANDARD":
                    variant = "COMPACT"
                    logo_width = 420
                    banner_height = 140

                elif variant == "COMPACT":
                    variant = "INFO_ONLY"

                if variant != "INFO_ONLY":
                    logo_width = min(
                        logo_width,
                        content_width,
                    )

                    logo_height = int(
                        logo.height
                        * logo_width
                        / logo.width
                    )

                    logo_height = min(
                        logo_height,
                        banner_height,
                    )

                    required = (
                        logo_height
                        + LAST_PAGE_BLOCK_GAP
                        + info_height
                    )

                    if required > free_height:
                        variant = "INFO_ONLY"

        except Exception:
            variant = "INFO_ONLY"

    cursor = (
        last_content_bottom
        + LAST_PAGE_BLOCK_GAP
    )

    drawn_banner = False

    if variant != "INFO_ONLY":
        try:
            with Image.open(
                LAST_PAGE_LOGO
            ) as source:
                logo = source.convert("RGBA")

            logo_width = min(
                logo_width,
                content_width,
            )

            logo_height = int(
                logo.height
                * logo_width
                / logo.width
            )

            logo_height = min(
                logo_height,
                banner_height,
            )

            logo = logo.resize(
                (
                    logo_width,
                    logo_height,
                ),
                Image.Resampling.LANCZOS,
            )

            logo_x = (
                MARGIN
                + (
                    content_width
                    - logo.width
                ) // 2
            )

            canvas.paste(
                logo,
                (
                    logo_x,
                    cursor,
                ),
                logo,
            )

            cursor += (
                logo.height
                + LAST_PAGE_BLOCK_GAP
            )

            drawn_banner = True

        except Exception as exc:
            print(
                "[WARN] Last-page banner failed:",
                exc,
            )

            variant = "INFO_ONLY"

            cursor = (
                last_content_bottom
                + LAST_PAGE_BLOCK_GAP
            )

    info_bottom = _draw_last_page_info(
        canvas,
        draw,
        top=cursor,
        width=content_width,
    )

    if info_bottom is None:
        return {
            "drawn": drawn_banner,
            "variant": variant,
            "free_height": free_height,
            "info_height": info_height,
        }

    return {
        "drawn": True,
        "variant": variant,
        "free_height": free_height,
        "info_height": info_height,
        "banner": drawn_banner,
        "bottom": info_bottom,
    }


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
    """
    News photography is intentionally disabled.

    Mobile uses a text-first editorial format.
    """
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
    """
    Return the canonical event sequence for Mobile rendering.

    For production editions, mobile_audio["events"] is the authoritative
    ordered event list. The grouped top/main/brief fields are presentation
    subsets of that same list and must not be concatenated again.

    The legacy fallback preserves compatibility with older/minimal edition
    structures that do not provide mobile_audio["events"].
    """
    mobile_audio = edition.get("mobile_audio")

    if isinstance(mobile_audio, dict):
        events = mobile_audio.get("events")

        if isinstance(events, list):
            return [
                event
                for event in events
                if isinstance(event, dict)
            ]

        result = []
        seen = set()

        def add_event(event):
            if not isinstance(event, dict):
                return

            key = id(event)

            if key in seen:
                return

            result.append(event)
            seen.add(key)

        top = mobile_audio.get("top_story")
        add_event(top)

        for key in (
            "main_stories",
            "briefs",
        ):
            value = mobile_audio.get(key)

            if isinstance(value, list):
                for event in value:
                    add_event(event)

        return result

    result = []
    seen = set()

    def add_event(event):
        if not isinstance(event, dict):
            return

        key = id(event)

        if key in seen:
            return

        result.append(event)
        seen.add(key)

    top = edition.get("top_story")
    add_event(top)

    for key in (
        "main_stories",
        "briefs",
        "additional_events",
        "remaining_events",
        "overflow_events",
    ):
        value = edition.get(key)

        if isinstance(value, list):
            for event in value:
                add_event(event)

    return result


def _event_card_label(event: dict) -> str:
    """Return the automatic editorial topic for a news card."""

    if not isinstance(event, dict):
        return "WORLD"

    content = event.get("content")

    # Use the automatically classified editorial section first.
    if isinstance(content, dict):
        section = _safe_text(content.get("section"))

        if section:
            aliases = {
                "world": "WORLD",
                "geopolitics": "GEOPOLITICS",
                "politics": "GEOPOLITICS",
                "business": "BUSINESS",
                "economy": "BUSINESS",
                "economic": "BUSINESS",
                "energy": "ENERGY",
                "technology": "TECHNOLOGY",
                "tech": "TECHNOLOGY",
                "science": "SCIENCE & HEALTH",
                "health": "SCIENCE & HEALTH",
                "science_health": "SCIENCE & HEALTH",
                "science & health": "SCIENCE & HEALTH",
                "climate": "CLIMATE",
                "environment": "CLIMATE",
                "trade": "TRADE & LOGISTICS",
                "logistics": "TRADE & LOGISTICS",
                "trade_logistics": "TRADE & LOGISTICS",
                "society": "SOCIETY",
                "social": "SOCIETY",
                "culture": "CULTURE",
                "arts": "CULTURE",
                "sports": "SPORTS",
                "sport": "SPORTS",
            }

            label = aliases.get(
                section.strip().lower()
            )

            if label:
                return label

    # Final fallback to the existing section/category logic.
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
    compact: bool = True,
) -> int:
    """
    Calculate the exact height of a text-only mobile story card.

    Mobile production is currently text-first:
    no story photographs are rendered.

    The same geometry is used during pagination and final drawing,
    so a card can never overflow into the next UI block.
    """

    if not isinstance(event, dict):
        return 190

    probe = Image.new(
        "RGB",
        (WIDTH, MOBILE_PAGE_HEIGHT),
        NEWSPAPER,
    )

    probe_draw = ImageDraw.Draw(probe)

    title_font = _font(20, bold=True)
    summary_font = _font(13)
    source_font = _font(11)

    title_max_lines = 2
    summary_max_lines = 3

    card_inner_width = (
        WIDTH
        - MARGIN * 2
        - 32
    )

    title_lines = _wrap(
        probe_draw,
        _title(event),
        title_font,
        card_inner_width,
    )[:title_max_lines]

    title_line_height = (
        title_font.getbbox("Ag")[3]
        - title_font.getbbox("Ag")[1]
        + 4
    )

    summary = _summary(event)

    summary_lines = []

    if summary:
        summary_lines = _wrap(
            probe_draw,
            summary,
            summary_font,
            card_inner_width,
        )[:summary_max_lines]

    summary_line_height = (
        summary_font.getbbox("Ag")[3]
        - summary_font.getbbox("Ag")[1]
        + 4
    )

    sources = _sources(event)

    source_lines = []

    if sources:
        source_text = "  •  ".join(
            sources[:3]
        )

        source_lines = _wrap(
            probe_draw,
            source_text,
            source_font,
            max(
                1,
                card_inner_width - 55,
            ),
        )[:2]

    source_line_height = (
        source_font.getbbox("Ag")[3]
        - source_font.getbbox("Ag")[1]
        + 2
    )

    # Header band.
    height = 35 + 15

    # Headline.
    if title_lines:
        height += (
            len(title_lines)
            * title_line_height
        )
        height += 7

    # Summary.
    if summary_lines:
        height += (
            len(summary_lines)
            * summary_line_height
        )
        height += 7

    # Source.
    if source_lines:
        height += max(
            18,
            len(source_lines)
            * source_line_height,
        )

    # Bottom padding.
    height += 14

    # Keep every card readable and predictable.
    return max(
        175,
        min(
            300,
            height,
        ),
    )


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
    footer_height = 300
    red_bar_height = 28

    # PAGE 01: full branded header + full footer.
    # PAGES 02+: compact header + bottom red stripe only.
    # Each page uses the real vertical space available to its layout.
    content_top_first = header_height - 61
    content_top_other = MARGIN + 50

    # PAGE 01 keeps a small controlled breathing room before
    # MARKETS TODAY while allowing additional compact stories.
    content_bottom_first = 930

    content_bottom_other = (
        MOBILE_PAGE_HEIGHT
        - red_bar_height
        - MARGIN
    )

    available_first = (
        content_bottom_first
        - content_top_first
    )

    available_other = (
        content_bottom_other
        - content_top_other
    )

    # A page with no stories is still a valid mobile edition.
    #
    # Pagination is determined by measured card height.
    # There is NO fixed story count per page.
    #
    # Rules:
    # - stories are never split;
    # - PAGE 01 has its larger branded header and footer;
    # - PAGE 02+ uses the compact header/footer;
    # - a story moves to the next page when the complete card
    #   no longer fits in the remaining vertical space.

    pages: list[list[dict]] = []

    current_page: list[dict] = []
    current_height = 0
    page_index = 0

    for event in events:

        # All mobile cards use the same compact visual language.
        compact = True

        event_height = _card_height(
            event,
            compact=compact,
        )

        available = (
            available_first
            if page_index == 0
            else available_other
        )

        required_height = event_height

        if current_page:
            required_height += CARD_GAP

        # If the complete card does not fit, start a new page.
        if (
            current_page
            and current_height + required_height > available
        ):
            pages.append(current_page)

            current_page = []
            current_height = 0
            page_index += 1

            available = available_other
            required_height = event_height

        current_page.append(event)
        current_height += required_height

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

                    # Center MORNING BRIEFING inside the open gap
                    # between the two interrupted top header lines.
                    gap_left = 624
                    gap_right = 814

                    briefing_x = (
                        gap_left
                        + (
                            gap_right
                            - gap_left
                            - briefing_width
                        ) // 2
                    )

                    draw.text(
                        (
                            briefing_x,
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
        # -------------------------------------------------------------
        # FOOTER
        # PAGE 1  -> assets/footer.png
        # PAGE 2+ -> assets/footer-pages.png
        # -------------------------------------------------------------

        footer_path = (
            Path("assets/footer.png")
            if page_number == 1
            else Path("assets/footer-pages.png")
        )

        if not footer_path.exists():
            return

        try:
            with Image.open(footer_path) as source:
                footer = source.convert("RGBA")

            # ---------------------------------------------------------
            # Remove transparent margins.
            # ---------------------------------------------------------

            alpha = footer.getchannel("A")
            bbox = alpha.getbbox()

            if bbox is None:
                return

            footer = footer.crop(bbox)

            # ---------------------------------------------------------
            # PAGE 1:
            # Remove everything below the red bottom stripe.
            # In the original footer asset the stripe ends around Y=514.
            # ---------------------------------------------------------

            if page_number == 1:
                red_bottom = min(515, footer.height)
                footer = footer.crop(
                    (
                        0,
                        0,
                        footer.width,
                        red_bottom,
                    )
                )

            # ---------------------------------------------------------
            # Fit the footer to the mobile page width.
            # ---------------------------------------------------------

            footer = ImageOps.contain(
                footer,
                (
                    WIDTH,
                    footer_height,
                ),
                method=Image.Resampling.LANCZOS,
            )

            # ---------------------------------------------------------
            # Align the visible footer exactly to the bottom edge.
            # ---------------------------------------------------------

            footer_top = MOBILE_PAGE_HEIGHT - footer.height

            
            canvas.paste(
                footer,
                (
                    (WIDTH - footer.width) // 2,
                    footer_top,
                ),
                footer,
            )

            # =========================================================
            # READY QR CODE OVERLAY
            # =========================================================

            qr_path = Path("assets/qr_code.png")

            if page_number == 1 and qr_path.exists():
                try:
                    with Image.open(qr_path) as source:
                        qr = ImageOps.contain(
                            source.convert("RGBA"),
                            (118, 118),   # размер QR — меняйте здесь
                            method=Image.Resampling.LANCZOS,
                        )

                    # -------------------------------------------------
                    # POSITION — меняйте X / Y здесь
                    # -------------------------------------------------

                    qr_x = 777
                    qr_y = 1058

                    canvas.paste(
                        qr,
                        (
                            qr_x,
                            qr_y,
                        ),
                        qr,
                    )

                except Exception as exc:
                    print(
                        f"[WARN] QR overlay failed: {exc}"
                    )

            return footer_top            

        except Exception as exc:
            print(f"[WARN] Failed to draw footer: {exc}")

            
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
            font=_font(17, bold=True),
            fill=RED,
        )

        # -------------------------------------------------------------
        # ROW 1 — INDEXES
        # -------------------------------------------------------------
        row1_y = y + 22

        label = "INDEXES"

        draw.text(
            (MARGIN, row1_y),
            label,
            font=_font(12, bold=True),
            fill=BLACK,
        )

        label_bbox = draw.textbbox(
            (MARGIN, row1_y),
            label,
            font=_font(12, bold=True),
        )

        data_x = label_bbox[2] + 10

        draw.text(
            (data_x, row1_y),
            "S&P 500  7,747.71  +1.06%   |   NASDAQ  26,584.06  +1.40%   |   DOW  53,686.11  +1.18%",
            font=_font(11),
            fill=GRAY,
        )

        # -------------------------------------------------------------
        # ROW 2 — COMMODITIES
        # -------------------------------------------------------------
        row2_y = y + 40

        label = "COMMODITIES"

        draw.text(
            (MARGIN, row2_y),
            label,
            font=_font(12, bold=True),
            fill=BLACK,
        )

        label_bbox = draw.textbbox(
            (MARGIN, row2_y),
            label,
            font=_font(12, bold=True),
        )

        data_x = label_bbox[2] + 10

        draw.text(
            (data_x, row2_y),
            "BRENT  $95.69  +0.46%   |   GOLD  $4,520.40  +0.96%   |   WTI  $91.71  +1.01%",
            font=_font(11),
            fill=GRAY,
        )

        # -------------------------------------------------------------
        # ROW 3 — CURRENCY / GLOBAL
        # -------------------------------------------------------------
        row3_y = y + 58

        label = "CURRENCY / GLOBAL"

        draw.text(
            (MARGIN, row3_y),
            label,
            font=_font(12, bold=True),
            fill=BLACK,
        )

        label_bbox = draw.textbbox(
            (MARGIN, row3_y),
            label,
            font=_font(12, bold=True),
        )

        data_x = label_bbox[2] + 10

        draw.text(
            (data_x, row3_y),
            "EUR/USD  1.1627   |   DXY  99.12  +0.27%   |   USD/CNY  6.7113  -0.11%",
            font=_font(11),
            fill=GRAY,
        )

        # -------------------------------------------------------------
        # ROW 4 — MARKET LEADERS
        # -------------------------------------------------------------
        row4_y = y + 76

        label = "MARKET LEADERS"

        draw.text(
            (MARGIN, row4_y),
            label,
            font=_font(12, bold=True),
            fill=BLACK,
        )

        label_bbox = draw.textbbox(
            (MARGIN, row4_y),
            label,
            font=_font(12, bold=True),
        )

        data_x = label_bbox[2] + 10

        draw.text(
            (data_x, row4_y),
            "NVIDIA  +1.80%   |   APPLE  +1.00%   |   TESLA  +5.42%",
            font=_font(11),
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
            page_available_height = available_first
        else:
            y = content_top_other
            page_available_height = available_other

        base_heights = []

        for event_index, event in enumerate(page_events):
            compact = (
                sum(
                    len(previous_page)
                    for previous_page in pages[: page_number - 1]
                )
                + event_index
                > 0
            )

            base_heights.append(
                _card_height(
                    event,
                    compact=compact,
                )
            )

        for index, event in enumerate(page_events):
            story_number = sum(
                len(previous_page)
                for previous_page in pages[: page_number - 1]
            ) + index + 1

            # One consistent mobile card layout on every page.
            compact = True

            # Use the content-driven height directly.
            # Do not stretch short stories to fill the page.
            card_height = base_heights[index]

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
                summary_font = _font(18)
                summary_max_lines = 2
                summary_spacing = 4
                image_title_gap = 10
                title_summary_gap = 7
                image_top_offset = 50
                summary_source_gap = 7
            else:
                image_height = 180
                title_font = _font(20, bold=True)
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

            image_width = 245 if compact else 285
            image_gap = 18

            image_left = (
                card_inner_right
                - image_width
            )

            text_x = card_inner_left

            # No photo -> use the entire card width.
            # Photo -> reserve the right column.
            if has_image:
                text_width = (
                    image_left
                    - image_gap
                    - text_x
                )
            else:
                text_width = (
                    card_inner_right
                    - text_x
                )

            if has_image:
                summary_probe = _wrap(
                    draw,
                    _summary(event),
                    _font(14 if compact else 18),
                    max(1, text_width),
                )

                summary_count = len(
                    summary_probe[:3 if compact else 5]
                )

                if compact:
                    image_height = (
                        105 if summary_count <= 1
                        else 125 if summary_count == 2
                        else 145
                    )
                else:
                    image_height = (
                        145 if summary_count <= 1
                        else 175 if summary_count == 2
                        else 205
                    )

                image_height = min(
                    image_height,
                    max(1, card_height - 58),
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

                # -----------------------------------------------------
                # SOURCE BLOCK — anchored to the bottom of the card.
                # -----------------------------------------------------
                source_font = _font(11)

                source_lines = _wrap(
                    draw,
                    source_text,
                    source_font,
                    text_width,
                )[:2]

                source_line_height = (
                    source_font.getbbox("Ag")[3]
                    - source_font.getbbox("Ag")[1]
                    + 2
                )

                source_gap = 4
                source_bottom_padding = 10

                source_text_height = (
                    max(1, len(source_lines))
                    * source_line_height
                )

                source_block_height = (
                    11 + source_gap + source_text_height
                )

                sources_y = (
                    card_bottom
                    - source_bottom_padding
                    - source_block_height
                )

                # SOURCE label.
                draw.text(
                    (
                        text_x,
                        sources_y,
                    ),
                    "SOURCE",
                    font=_font(11, bold=True),
                    fill=RED,
                )

                # Source name.
                _draw_wrapped(
                    draw,
                    source_text,
                    text_x,
                    sources_y + 11 + source_gap,
                    source_font,
                    GRAY,
                    text_width,
                    max_lines=2,
                    spacing=2,
                )

            y = card_bottom + CARD_GAP

        # -------------------------------------------------------------
        # PAGE 01 — MARKETS TODAY + FULL FOOTER
        # -------------------------------------------------------------

        if page_number == 1:

            # Keep MARKETS TODAY closer to the footer so more
            # vertical space remains available for news cards.
            markets_y = MOBILE_PAGE_HEIGHT - footer_height + 50

            draw_markets_today(
                canvas,
                draw,
                markets_y,
            )

            footer_top = draw_footer(
                canvas,
                draw,
                page_number,
            )

            if footer_top is not None:
                draw.line(
                    (
                        0,
                        footer_top - 2,
                        WIDTH,
                        footer_top - 2,
                    ),
                    fill=BLACK,
                    width=3,
                )

        # -------------------------------------------------------------
        # PAGES 2+ — DEDICATED FOOTER IMAGE
        # -------------------------------------------------------------

        else:

            footer_top = draw_footer(
                canvas,
                draw,
                page_number,
            )

        # -------------------------------------------------------------
        # LAST PAGE BRANDING
        # -------------------------------------------------------------

        if page_number == len(pages):
            if page:
                last_content_bottom = (
                    y - CARD_GAP
                )
            else:
                last_content_bottom = (
                    content_top_first
                    if page_number == 1
                    else content_top_other
                )

            if page_number == 1:
                # MARKETS TODAY occupies the lower part of PAGE 01.
                available_bottom = (
                    min(
                        footer_top - LAST_PAGE_FOOTER_GAP,
                        markets_y - 24,
                    )
                )
            else:
                available_bottom = (
                    footer_top - LAST_PAGE_FOOTER_GAP
                )

            branding_result = _draw_last_page_branding(
                canvas,
                draw,
                last_content_bottom=last_content_bottom,
                available_bottom=available_bottom,
            )

            print(
                "DEBUG LAST PAGE BRANDING:",
                f"page={page_number}",
                f"free_height={branding_result.get('free_height')}",
                f"info_height={branding_result.get('info_height')}",
                f"variant={branding_result.get('variant')}",
                f"banner={branding_result.get('banner', False)}",
                f"drawn={branding_result.get('drawn', False)}",
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
