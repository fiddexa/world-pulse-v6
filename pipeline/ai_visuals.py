"""
AROUND THE MAIN v6 — AI Editorial Visuals

Free image generation through AI Horde.

The AI creates the editorial image.
AROUND THE MAIN branding and protection notice are applied
programmatically with Pillow.

ONE EVENT -> ONE IMAGE ASSET -> FULL + MOBILE + TELEGRAM
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


AI_HORDE_BASE_URL = (
    os.getenv(
        "AI_HORDE_BASE_URL",
        "https://stablehorde.net/api/v2",
    ).rstrip("/")
)

# Anonymous AI Horde key is officially supported.
# A personal key can later be supplied through AI_HORDE_API_KEY.
AI_HORDE_API_KEY = os.getenv(
    "AI_HORDE_API_KEY",
    "0000000000",
).strip()

OUTPUT_DIR = Path(
    os.getenv(
        "AI_VISUAL_OUTPUT_DIR",
        "data/images/ai",
    )
)

REQUEST_TIMEOUT = int(
    os.getenv(
        "AI_HORDE_TIMEOUT",
        "30",
    )
)

MAX_WAIT_SECONDS = int(
    os.getenv(
        "AI_HORDE_MAX_WAIT",
        "300",
    )
)

POLL_SECONDS = int(
    os.getenv(
        "AI_HORDE_POLL_SECONDS",
        "4",
    )
)

WIDTH = 1024
HEIGHT = 576


BRAND_NAME = "AROUND THE MAIN"
HANDLE = "@aroundthemain"

PROTECTION_LINE = (
    "© ALL IMAGES ARE AI-GENERATED AND PROTECTED"
)

PROTECTION_SUBLINE = (
    "UNAUTHORIZED USE IS PROHIBITED"
)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _first_text(event: dict, *keys: str) -> str:
    for key in keys:
        value = _safe_text(event.get(key))
        if value:
            return value

    content = event.get("content")

    if isinstance(content, dict):
        for key in keys:
            value = _safe_text(content.get(key))
            if value:
                return value

    return ""


def _list_text(event: dict, key: str) -> list[str]:
    value = event.get(key)

    if not isinstance(value, list):
        return []

    result = []

    for item in value:
        if isinstance(item, dict):
            text = (
                _safe_text(item.get("name"))
                or _safe_text(item.get("title"))
            )
        else:
            text = _safe_text(item)

        if text and text not in result:
            result.append(text)

    return result


def build_visual_prompt(event: dict) -> str:
    """
    Build a concise, factual editorial visual prompt from the event.

    The AI generates only the photographic scene.
    All AROUND THE MAIN branding is applied later by Pillow.
    """

    title = _first_text(
        event,
        "title",
        "headline",
        "publication_title",
        "display_title",
    )

    summary = _first_text(
        event,
        "summary",
        "publication_summary",
        "description",
        "dek",
    )

    content = event.get("content")

    why_it_matters = ""

    if isinstance(content, dict):
        why_it_matters = _safe_text(
            content.get("why_it_matters")
        )

    category = _safe_text(
        event.get("category")
    )

    locations = _list_text(
        event,
        "locations",
    )

    actors = _list_text(
        event,
        "actors",
    )

    parts = [
        "Create a high-quality photorealistic editorial news visual "
        "for AROUND THE MAIN.",
        "Show a clear, recognizable scene representing the central "
        "subject of the verified news story.",
        "Use realistic contemporary international-news photography, "
        "natural lighting, authentic environments, realistic people "
        "and objects, credible composition, and strong visual "
        "storytelling.",
        "The image must be visually specific to the actual event "
        "subject, but must not invent material facts that are not "
        "supported by the supplied information.",
        "Do not create an abstract texture, generic crowd, symbolic "
        "image, fantasy scene, cinematic poster, or unrelated stock "
        "scene unless the verified story itself requires it.",
        "Do not place any words, captions, headlines, logos, "
        "watermarks, social-media icons, interface elements, or "
        "typography inside the generated scene.",
        "Do not imitate or reproduce an existing news photograph.",
        "Create an original editorial image suitable for publication.",
    ]

    if title:
        parts.append(
            f"Verified news headline: {title}"
        )

    if summary:
        parts.append(
            f"Verified news summary: {summary}"
        )

    if why_it_matters:
        parts.append(
            f"Why it matters: {why_it_matters}"
        )

    if category:
        parts.append(
            f"Editorial section: {category}"
        )

    if locations:
        parts.append(
            "Relevant locations: "
            + ", ".join(locations[:5])
        )

    if actors:
        parts.append(
            "Relevant people or entities: "
            + ", ".join(actors[:5])
        )

    parts.append(
        "Wide 16:9 editorial composition. "
        "Keep the lower-right corner visually calm and relatively "
        "uncluttered so that the publication's own branding can be "
        "added later."
    )

    return "\n".join(parts)


def _request_json(
    method: str,
    url: str,
    payload: dict | None = None,
) -> dict:
    data = None

    headers = {
        "Accept": "application/json",
        "User-Agent": "AroundTheMain/1.0",
    }

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    with urllib.request.urlopen(
        request,
        timeout=REQUEST_TIMEOUT,
    ) as response:
        body = response.read()

    if not body:
        raise RuntimeError(
            "AI Horde returned an empty response"
        )

    return json.loads(
        body.decode(
            "utf-8",
            errors="replace",
        )
    )


def _download_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AroundTheMain/1.0",
            "Accept": "image/*",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=REQUEST_TIMEOUT,
    ) as response:
        data = response.read()

    if not data:
        raise RuntimeError(
            "AI Horde image response was empty"
        )

    return data


def _font(size: int, bold: bool = False):
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
            return ImageFont.truetype(
                str(path),
                size,
            )

    return ImageFont.load_default()


def apply_branding(image: Image.Image) -> Image.Image:
    """
    Apply the permanent AROUND THE MAIN visual identity.

    Two branding placements are used:
    1. compact brand mark near the upper-left;
    2. full protection block in the lower-right.

    No messenger or social-media icons are used.
    """

    image = image.convert("RGBA")

    overlay = Image.new(
        "RGBA",
        image.size,
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(
        overlay,
        "RGBA",
    )

    width, height = image.size

    margin = max(
        24,
        int(width * 0.032),
    )

    # ============================================================
    # TOP BRAND
    # ============================================================

    top_x = margin
    top_y = margin

    top_panel_right = (
        top_x
        + int(width * 0.30)
    )

    top_panel_bottom = (
        top_y
        + int(height * 0.085)
    )

    draw.rounded_rectangle(
        (
            top_x,
            top_y,
            top_panel_right,
            top_panel_bottom,
        ),
        radius=max(8, width // 120),
        fill=(0, 0, 0, 125),
    )

    top_font = _font(
        max(20, int(width * 0.032)),
        bold=True,
    )

    draw.text(
        (
            top_x + int(width * 0.018),
            top_y + int(height * 0.012),
        ),
        BRAND_NAME,
        font=top_font,
        fill=(255, 255, 255, 245),
    )

    # ============================================================
    # LOWER-RIGHT PROTECTION BLOCK
    # ============================================================

    panel_width = int(
        width * 0.42
    )

    panel_height = int(
        height * 0.235
    )

    left = (
        width
        - panel_width
        - margin
    )

    top = (
        height
        - panel_height
        - margin
    )

    right = width - margin
    bottom = height - margin

    draw.rounded_rectangle(
        (
            left,
            top,
            right,
            bottom,
        ),
        radius=max(10, width // 100),
        fill=(0, 0, 0, 150),
    )

    inner_x = (
        left
        + int(width * 0.020)
    )

    inner_right = (
        right
        - int(width * 0.020)
    )

    brand_font = _font(
        max(20, int(width * 0.030)),
        bold=True,
    )

    protection_font = _font(
        max(10, int(width * 0.0125)),
        bold=True,
    )

    subline_font = _font(
        max(8, int(width * 0.010)),
        bold=False,
    )

    handle_font = _font(
        max(12, int(width * 0.017)),
        bold=True,
    )

    y = (
        top
        + int(height * 0.018)
    )

    draw.text(
        (inner_x, y),
        BRAND_NAME,
        font=brand_font,
        fill=(255, 255, 255, 255),
    )

    bbox = draw.textbbox(
        (0, 0),
        BRAND_NAME,
        font=brand_font,
    )

    brand_height = (
        bbox[3] - bbox[1]
    )

    line_y = (
        y
        + brand_height
        + int(height * 0.012)
    )

    draw.line(
        (
            inner_x,
            line_y,
            inner_right,
            line_y,
        ),
        fill=(255, 255, 255, 220),
        width=max(1, width // 650),
    )

    protection_y = (
        line_y
        + int(height * 0.014)
    )

    draw.text(
        (
            inner_x,
            protection_y,
        ),
        PROTECTION_LINE,
        font=protection_font,
        fill=(255, 255, 255, 245),
    )

    protection_bbox = draw.textbbox(
        (0, 0),
        PROTECTION_LINE,
        font=protection_font,
    )

    protection_height = (
        protection_bbox[3]
        - protection_bbox[1]
    )

    subline_y = (
        protection_y
        + protection_height
        + int(height * 0.006)
    )

    draw.text(
        (
            inner_x,
            subline_y,
        ),
        PROTECTION_SUBLINE,
        font=subline_font,
        fill=(255, 255, 255, 225),
    )

    subline_bbox = draw.textbbox(
        (0, 0),
        PROTECTION_SUBLINE,
        font=subline_font,
    )

    subline_height = (
        subline_bbox[3]
        - subline_bbox[1]
    )

    handle_y = (
        subline_y
        + subline_height
        + int(height * 0.010)
    )

    draw.text(
        (
            inner_x,
            handle_y,
        ),
        HANDLE,
        font=handle_font,
        fill=(255, 255, 255, 245),
    )

    return Image.alpha_composite(
        image,
        overlay,
    ).convert("RGB")


def _event_digest(event: dict) -> str:
    data = {
        "title": _first_text(
            event,
            "title",
            "headline",
        ),
        "summary": _first_text(
            event,
            "summary",
            "publication_summary",
        ),
        "why_it_matters": _first_text(
            event,
            "why_it_matters",
        ),
        "category": event.get("category"),
        "locations": event.get("locations"),
        "actors": event.get("actors"),
        "objects": event.get("objects"),
    }

    canonical = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:24]


def generate_ai_visual(event: dict) -> Path:
    """
    Generate and save one editorial visual for one event.

    Raises on generation failure.
    The caller must decide how to handle that failure.
    """

    if not isinstance(event, dict):
        raise ValueError(
            "event must be a dictionary"
        )

    prompt = build_visual_prompt(
        event
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    digest = _event_digest(
        event
    )

    output_path = (
        OUTPUT_DIR
        / f"{digest}.jpg"
    )

    # Deterministic reuse: never generate the same event twice.
    if (
        output_path.exists()
        and output_path.stat().st_size > 0
    ):
        return output_path

    payload = {
        "prompt": prompt,
        "params": {
            "width": WIDTH,
            "height": HEIGHT,
            "steps": 20,
            "n": 1,
        },
        "nsfw": False,
        "shared": False,
        "slow_workers": True,
    }

    if AI_HORDE_API_KEY:
        headers_payload = payload
    else:
        headers_payload = payload

    request_url = (
        f"{AI_HORDE_BASE_URL}"
        "/generate/async"
    )

    data = json.dumps(
        headers_payload
    ).encode("utf-8")

    request = urllib.request.Request(
        request_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "apikey": AI_HORDE_API_KEY,
            "Client-Agent": "AroundTheMain:1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
        ) as response:
            body = response.read()

    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"AI Horde HTTP {exc.code}: {detail}"
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"AI Horde connection failed: {exc.reason}"
        ) from exc

    response_data = json.loads(
        body.decode(
            "utf-8",
            errors="replace",
        )
    )

    request_id = _safe_text(
        response_data.get("id")
    )

    if not request_id:
        raise RuntimeError(
            "AI Horde did not return a generation ID"
        )

    # Use the lightweight CHECK endpoint while waiting.
    # Only request the full STATUS payload after generation is done.
    check_url = (
        f"{AI_HORDE_BASE_URL}"
        f"/generate/check/{request_id}"
    )

    status_url = (
        f"{AI_HORDE_BASE_URL}"
        f"/generate/status/{request_id}"
    )

    deadline = time.time() + MAX_WAIT_SECONDS
    poll_delay = max(4, POLL_SECONDS)
    max_poll_delay = 30

    while time.time() < deadline:
        try:
            check = _request_json(
                "GET",
                check_url,
            )

        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                retry_after = exc.headers.get(
                    "Retry-After"
                )

                try:
                    wait_seconds = max(
                        poll_delay,
                        int(retry_after)
                        if retry_after
                        else poll_delay,
                    )
                except (TypeError, ValueError):
                    wait_seconds = poll_delay

                time.sleep(
                    min(
                        wait_seconds,
                        max_poll_delay,
                    )
                )

                poll_delay = min(
                    poll_delay * 2,
                    max_poll_delay,
                )
                continue

            raise

        if check.get("faulted"):
            raise RuntimeError(
                "AI Horde generation failed"
            )

        if check.get("done"):
            # Generation is complete; now fetch the actual image URL.
            status = _request_json(
                "GET",
                status_url,
            )

            generations = status.get(
                "generations"
            )

            if not isinstance(
                generations,
                list,
            ) or not generations:
                raise RuntimeError(
                    "AI Horde completed without an image"
                )

            image_url = _safe_text(
                generations[0].get("img")
                if isinstance(
                    generations[0],
                    dict,
                )
                else ""
            )

            if not image_url:
                raise RuntimeError(
                    "AI Horde returned no image URL"
                )

            image_data = _download_bytes(
                image_url
            )

            try:
                with Image.open(
                    io.BytesIO(image_data)
                ) as source:
                    image = source.convert(
                        "RGB"
                    )

                    image = image.resize(
                        (WIDTH, HEIGHT),
                        Image.Resampling.LANCZOS,
                    )

            except Exception as exc:
                raise RuntimeError(
                    "AI Horde returned invalid image data"
                ) from exc

            image = apply_branding(
                image
            )

            image.save(
                output_path,
                format="JPEG",
                quality=94,
                optimize=True,
            )

            if (
                not output_path.exists()
                or output_path.stat().st_size == 0
            ):
                raise RuntimeError(
                    "AI visual file was not created"
                )

            return output_path

        time.sleep(
            POLL_SECONDS
        )

    raise TimeoutError(
        f"AI Horde generation timed out after "
        f"{MAX_WAIT_SECONDS} seconds"
    )


def attach_ai_visual(
    event: dict,
    *,
    required: bool = False,
) -> dict:
    """
    Return a copy of the event with its AI visual attached.

    `required=True` means generation failure is fatal.
    """

    result = dict(event)

    try:
        image_path = generate_ai_visual(
            result
        )

        result["image_path"] = str(
            image_path
        )

        result["image_generated"] = True
        result["image_provider"] = "AI_HORDE"
        result["image_provenance"] = (
            "AI-generated editorial visual"
        )
        result["image_generated_at"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        result["image_prompt_hash"] = hashlib.sha256(
            build_visual_prompt(
                result
            ).encode("utf-8")
        ).hexdigest()

        return result

    except Exception:
        if required:
            raise

        # Do not silently attach an unrelated image.
        result["image_generated"] = False
        result["image_generation_failed"] = True

        return result


def attach_ai_visuals(
    events: list[dict],
    *,
    required: bool = False,
) -> list[dict]:
    """
    Generate one visual per selected event.
    """

    if not isinstance(
        events,
        list,
    ):
        return []

    return [
        attach_ai_visual(
            event,
            required=required,
        )
        for event in events
        if isinstance(event, dict)
    ]


def attach_selected_ai_visuals(edition: dict, *, required: bool = False) -> dict:
    """
    Generate AI visuals only for the stories selected for Mobile/Audio.

    The selected events are the same event objects referenced by the Full
    Edition structure, so attaching image metadata here makes the same
    asset available to Full, Mobile and Telegram renderers.
    """
    mobile_audio = edition.get("mobile_audio") or {}
    selected_events = mobile_audio.get("events") or []

    generated = 0
    failed = 0

    for event in selected_events:
        result = attach_ai_visual(event, required=required)

        for key in (
            "image_path",
            "image_generated",
            "image_provider",
            "image_provenance",
            "image_generated_at",
            "image_prompt_hash",
            "image_generation_failed",
        ):
            if key in result:
                event[key] = result[key]

        if result.get("image_path"):
            generated += 1
        elif result.get("image_generation_failed"):
            failed += 1

    edition["ai_visuals"] = {
        "enabled": True,
        "selected_event_count": len(selected_events),
        "generated": generated,
        "failed": failed,
    }

    return edition
