"""
AROUND THE MAIN — Audio Script

Builds a deterministic spoken script from one edition.
No publication logic and no TTS provider logic live here.
"""
from __future__ import annotations

import re
from typing import Any


_EVENT_COLLECTION_KEYS = (
    "events",
    "main_stories",
    "briefs",
    "additional_events",
)


def _event_title(event: dict[str, Any]) -> str:
    if not isinstance(event, dict):
        return ""

    title = (
        event.get("title")
        or event.get("headline")
        or event.get("name")
        or ""
    )

    if title:
        return str(title).strip()

    articles = event.get("articles")

    if isinstance(articles, list):
        for article in articles:
            if not isinstance(article, dict):
                continue

            title = (
                article.get("title")
                or article.get("headline")
                or article.get("name")
                or ""
            )

            if title:
                return str(title).strip()

    content = event.get("content")

    if isinstance(content, dict):
        title = (
            content.get("title")
            or content.get("headline")
            or content.get("name")
            or ""
        )

        if title:
            return str(title).strip()

    return ""


def _event_summary(event: dict[str, Any]) -> str:
    if not isinstance(event, dict):
        return ""

    summary = (
        event.get("summary")
        or event.get("description")
        or event.get("text")
        or event.get("body")
        or ""
    )

    if summary:
        return str(summary).strip()

    articles = event.get("articles")

    if isinstance(articles, list):
        for article in articles:
            if not isinstance(article, dict):
                continue

            summary = (
                article.get("summary")
                or article.get("description")
                or article.get("text")
                or article.get("body")
                or ""
            )

            if summary:
                return str(summary).strip()

    content = event.get("content")

    if isinstance(content, dict):
        summary = (
            content.get("summary")
            or content.get("description")
            or content.get("text")
            or ""
        )

        if summary:
            return str(summary).strip()

    return ""


def _collect_events(edition: dict[str, Any]) -> list[dict[str, Any]]:
    mobile_audio = edition.get("mobile_audio")

    if isinstance(mobile_audio, dict):
        events: list[dict[str, Any]] = []
        seen: set[str] = set()

        def add_mobile_event(event: Any) -> None:
            if not isinstance(event, dict):
                return

            title = _event_title(event)
            if not title:
                return

            identity = (
                str(event.get("id") or "").strip()
                or title.lower()
            )

            if identity in seen:
                return

            seen.add(identity)
            events.append(event)

        for key in (
            "top_story",
            "main_stories",
            "briefs",
        ):
            value = mobile_audio.get(key)

            if isinstance(value, list):
                for event in value:
                    add_mobile_event(event)
            elif isinstance(value, dict):
                add_mobile_event(value)

        return events

    events: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_event(event: Any) -> None:
        if not isinstance(event, dict):
            return

        title = _event_title(event)
        if not title:
            return

        identity = (
            str(event.get("id") or "").strip()
            or title.lower()
        )

        if identity in seen:
            return

        seen.add(identity)
        events.append(event)

    for key in _EVENT_COLLECTION_KEYS:
        value = edition.get(key)

        if isinstance(value, list):
            for event in value:
                add_event(event)

    top_story = edition.get("top_story")

    if isinstance(top_story, dict):
        add_event(top_story)

    return events



def _clean_spoken_text(text: str) -> str:
    """
    Conservative deterministic cleanup for TTS.

    This layer only normalizes obvious textual artifacts.
    It does not rewrite editorial meaning or add facts.
    """

    if not text:
        return ""

    text = str(text).strip()

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    # Normalize apostrophes.
    text = text.replace("’", "'")

    # Fix immediate duplicated words:
    # "were were" -> "were"
    # "the the" -> "the"
    text = re.sub(
        r"\b([A-Za-z]+)\s+\1\b",
        r"\1",
        text,
        flags=re.IGNORECASE,
    )

    # Normalize common dash characters.
    text = text.replace("—", " - ")
    text = text.replace("–", " - ")
    text = text.replace("−", " - ")

    # Remove spaces before punctuation.
    text = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        text,
    )

    # Collapse repeated punctuation.
    text = re.sub(
        r"([.!?]){2,}",
        r"\1",
        text,
    )

    # Expand only the most common TTS-hostile abbreviations.
    replacements = {
        r"\bU\.S\.\b": "United States",
        r"\bU\.K\.\b": "United Kingdom",
        r"\bE\.U\.\b": "European Union",
        r"\bUAVs\b": "U A V's",
        r"\bUAVs\b": "U A V's",
    }

    for pattern, replacement in replacements.items():
        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE,
        )

    # Common lowercase possessive forms caused by source normalization.
    possessive_fixes = {
        "zelenskyys": "Zelensky's",
        "russias": "Russia's",
        "israels": "Israel's",
        "yemens": "Yemen's",
        "pyongyangs": "Pyongyang's",
        "myanmars": "Myanmar's",
        "nigerias": "Nigeria's",
        "malis": "Mali's",
        "houthis": "Houthis'",
        "heros": "hero's",
        "cages": "Cage's",
    }

    for wrong, correct in possessive_fixes.items():
        text = re.sub(
            rf"\b{re.escape(wrong)}\b",
            correct,
            text,
            flags=re.IGNORECASE,
        )

    # Add comma separators to obvious large integer values.
    def _comma_large_number(match: re.Match[str]) -> str:
        value = match.group(0)

        if len(value) < 4:
            return value

        return f"{int(value):,}"

    text = re.sub(
        r"(?<![A-Za-z0-9.,])\d{4,}(?![A-Za-z0-9.,])",
        _comma_large_number,
        text,
    )

    # Normalize simple currency and percentage notation for speech.
    text = re.sub(
        r"\$(\d+(?:\.\d+)?)",
        r"\1 dollars",
        text,
    )

    text = re.sub(
        r"(?<![\w])([0-9]+(?:\.[0-9]+)?)%",
        r"\1 percent",
        text,
    )

    # Improve singular/plural use for simple "number cent" cases.
    text = re.sub(
        r"\b(1) cent\b",
        r"\1 cent",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\b([2-9]\d*|1\d+) cent\b",
        r"\1 cents",
        text,
        flags=re.IGNORECASE,
    )

    return re.sub(r"\s+", " ", text).strip()


def _spoken_title(text: str) -> str:
    """
    Prepare a headline for spoken delivery.
    """

    text = _clean_spoken_text(text)

    if not text:
        return ""

    # Expand a few common headline conventions.
    text = re.sub(
        r"\bU\.S\.\b",
        "U.S.",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\bEU\b",
        "E.U.",
        text,
        flags=re.IGNORECASE,
    )

    # Keep headline semantics intact.
    text = text.rstrip(" .!?")

    return text + "."


def _spoken_summary(text: str) -> str:
    """
    Prepare a source summary for TTS.

    The summary is normalized exactly once through
    _clean_spoken_text(), then receives only speech-safe
    punctuation and spacing adjustments.
    """

    normalized = _clean_spoken_text(text)

    if not normalized:
        return ""

    # Currency / percentage symbols.
    normalized = normalized.replace(
        "%",
        " percent",
    )

    normalized = normalized.replace(
        "$",
        " dollars ",
    )

    # Clean whitespace introduced by symbol replacement.
    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()

    if normalized[-1] not in ".!?":
        normalized += "."

    return normalized

def _event_source(event: dict[str, Any]) -> str:
    """
    Return the primary source name from the first article in an event.
    The Edition structure stores source on article objects.
    """

    articles = event.get("articles")

    if not isinstance(articles, list):
        return ""

    for article in articles:
        if not isinstance(article, dict):
            continue

        source = str(
            article.get("source") or ""
        ).strip()

        if source:
            return source

    return ""


def _spoken_source(source: str) -> str:
    """
    Convert the internal source identifier to a natural spoken attribution.
    """

    key = str(source or "").strip().lower()

    mapping = {
        "bbc": "According to BBC.",
        "africanews": "According to Africanews.",
        "euronews": "According to Euronews.",
        "dw": "According to DW.",
        "un": "According to the United Nations.",
    }

    return mapping.get(
        key,
        "",
    )


def _summary_has_attribution(text: str) -> bool:
    """
    Avoid adding a second source attribution when the summary
    already contains an explicit reporting attribution.
    """

    value = str(text or "").strip().lower()

    if not value:
        return False

    attribution_patterns = (
        "reports",
        "reported",
        "report says",
        "report said",
        "reports say",
        "reports said",
        "officials say",
        "officials said",
        "officials tell",
        "officials told",
        "experts say",
        "experts said",
        "aid groups say",
        "aid groups said",
        "police say",
        "police said",
        "government says",
        "government said",
        "the ministry says",
        "the ministry said",
        "the agency says",
        "the agency said",
        "the u.n. says",
        "the u.n. said",
        "the united nations says",
        "the united nations said",
    )

    return any(
        pattern in value
        for pattern in attribution_patterns
    )

def build_audio_script(edition: dict[str, Any]) -> str:
    """
    Build a deterministic spoken script.

    For the legacy minimal `events` structure, preserve the exact
    existing output contract used by the test suite.

    For the richer production edition structure, return a complete
    English spoken briefing.
    """
    if not isinstance(edition, dict):
        raise ValueError("edition must be a dictionary")

    events = edition.get("events")

    # Preserve the existing public/test contract.
    if (
        isinstance(events, list)
        and events
        and not any(
            key in edition
            for key in (
                "main_stories",
                "briefs",
                "additional_events",
                "top_story",
            )
        )
    ):
        lines: list[str] = []

        edition_label = str(
            edition.get("edition_label")
            or "AROUND THE MAIN"
        ).strip()

        lines.append(edition_label)

        for index, event in enumerate(events, start=1):
            if not isinstance(event, dict):
                continue

            title = _event_title(event)
            summary = _event_summary(event)

            if not title:
                continue

            lines.append(f"{index}. {title}")

            if summary:
                lines.append(summary)

        return "\n\n".join(lines).strip()

    # Production format.
    edition_label = str(
        edition.get("edition_label")
        or edition.get("edition_name")
        or edition.get("edition_id")
        or ""
    ).strip()

    production_events = _collect_events(
        edition
    )

    lines: list[str] = [
        "AROUND THE MAIN.",
    ]

    publication_date = str(
        edition.get("publication_date")
        or ""
    ).strip()

    if publication_date:
        try:
            from datetime import date

            parsed_date = date.fromisoformat(
                publication_date
            )

            spoken_date = parsed_date.strftime(
                "%B %d, %Y"
            ).replace(" 0", " ")

            lines.append(
                f"{spoken_date}."
            )
        except ValueError:
            lines.append(
                f"{publication_date}."
            )
    elif edition_label:
        lines.append(
            f"{edition_label}."
        )

    for index, event in enumerate(
        production_events,
        start=1,
    ):
        title = _spoken_title(
            _event_title(event)
        )

        raw_summary = _event_summary(event)

        summary = _spoken_summary(
            raw_summary
        )

        source = _spoken_source(
            _event_source(event)
        )

        if not title:
            continue

        lines.append(
            f"Story {index}."
        )

        lines.append(
            title
        )

        if summary:
            lines.append(
                summary
            )

        if (
            source
            and not _summary_has_attribution(
                raw_summary
            )
        ):
            lines.append(
                source
            )

    lines.append(
        "That was Around the Main."
    )

    lines.append(
        "Stay informed. Stay ahead."
    )

    return "\n\n".join(
        line.strip()
        for line in lines
        if line.strip()
    ).strip()
