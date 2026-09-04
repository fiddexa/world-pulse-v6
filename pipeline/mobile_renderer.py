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
X_HANDLE = "@aroundthemain"

RED = (190, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (105, 105, 105)
LIGHT_GRAY = (225, 225, 225)
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
    Compact mobile newspaper card height.

    The card must remain compact while leaving enough room
    for title, summary and sources inside the border.
    """

    if _has_real_image(event):
        return 300

    return 200


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

    header_height = 285
    footer_height = 300

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

    for event in events:
        event_height = _card_height(event)

        required = event_height

        if current_page:
            required += CARD_GAP

        if (
            current_page
            and current_height + required > available_first
        ):
            pages.append(current_page)
            current_page = []
            current_height = 0
            required = event_height

        current_page.append(event)
        current_height += required

    if current_page:
        pages.append(current_page)

    if not pages:
        pages = [[]]

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
                width=1,
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

            footer = ImageOps.contain(
                footer,
                (
                    WIDTH - MARGIN * 2,
                    footer_height,
                ),
                Image.Resampling.LANCZOS,
            )

            footer_x = (WIDTH - footer.width) // 2
            footer_y = MOBILE_PAGE_HEIGHT - footer.height

            canvas.paste(
                footer,
                (
                    footer_x,
                    footer_y,
                ),
            )

        except Exception:
            pass

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
            card_height = _card_height(event)

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

            category = _event_category(event)

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

            # Global story number.
            story_number = sum(
                len(previous_page)
                for previous_page in pages[: page_number - 1]
            ) + index + 1

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

            if has_image:
                image_top = card_top + 58
                image_height = 180

                image = _load_image(
                    event,
                    text_width,
                    image_height,
                )

                canvas.paste(
                    image,
                    (
                        text_x,
                        image_top,
                    ),
                )

                title_y = (
                    image_top
                    + image_height
                    + 22
                )
            else:
                title_y = card_top + 45

            title_end = _draw_wrapped(
                draw,
                _title(event),
                text_x,
                title_y,
                _font(30, bold=True),
                BLACK,
                text_width,
                max_lines=4,
                spacing=5,
            )

            current_y = title_end + 12

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

                current_y = summary_end + 15

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

            y = card_bottom + CARD_GAP

        draw_footer(
            canvas,
            draw,
            page_number,
        )

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
