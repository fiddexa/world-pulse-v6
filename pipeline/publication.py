"""
AROUND THE MAIN v6 - Publication Layer

Prepares deterministic channel-specific publication payloads from
already-processed content.

This layer does not invent facts and does not publish externally.
"""


def _safe_text(value):
    if value is None:
        return ""

    return str(value).strip()


def _content(event):
    if not isinstance(event, dict):
        return {}

    value = event.get("content")

    if isinstance(value, dict):
        return value

    return {}


def _telegram_text(event):
    content = _content(event)

    headline = _safe_text(content.get("headline"))
    summary = _safe_text(content.get("summary"))
    verification = _safe_text(content.get("verification"))

    sources = content.get("sources")

    if not isinstance(sources, list):
        sources = []

    parts = []

    if headline:
        parts.append(headline)

    if summary:
        parts.append(summary)

    if verification:
        parts.append(
            f"Verification: {verification}"
        )

    if sources:
        parts.append(
            "Sources: "
            + ", ".join(
                _safe_text(source)
                for source in sources
                if _safe_text(source)
            )
        )

    return "\n\n".join(parts)


def _website(event):
    content = _content(event)

    sources = content.get("sources")
    if not isinstance(sources, list):
        sources = []

    affected_areas = content.get("affected_areas")
    if not isinstance(affected_areas, list):
        affected_areas = []

    summary = _safe_text(
        content.get("summary")
    )

    return {
        "headline": _safe_text(
            content.get("headline")
        ),
        "summary": summary,
        "body": summary,
        "section": (
            _safe_text(content.get("section"))
            or "world"
        ),
        "verification": (
            _safe_text(
                content.get("verification")
            )
            or "UNCONFIRMED"
        ),
        "sources": [
            _safe_text(source)
            for source in sources
            if _safe_text(source)
        ],
        "published_at": _safe_text(
            content.get("published_at")
        ),
        "affected_areas": [
            _safe_text(area)
            for area in affected_areas
            if _safe_text(area)
        ],
    }


def build_publication(event):
    """
    Build channel-specific publication payloads.

    The original event is never modified.
    """

    if not isinstance(event, dict):
        return {}

    result = dict(event)

    result["publication"] = {
        "telegram": _telegram_text(event),
        "website": _website(event),
    }

    return result


def build_publications(events):
    """
    Build publication payloads for multiple events.
    """

    if not isinstance(events, list):
        return []

    return [
        build_publication(event)
        for event in events
        if isinstance(event, dict)
    ]
