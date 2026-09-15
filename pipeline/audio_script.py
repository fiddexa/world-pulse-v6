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
    """
    Return the canonical Mobile/Audio event sequence.

    For production editions, mobile_audio["events"] is the single
    authoritative ordered event list shared by Mobile and Audio.

    Legacy/minimal editions keep the previous compatibility fallback.
    """

    mobile_audio = edition.get("mobile_audio")

    if isinstance(mobile_audio, dict):
        canonical_events = mobile_audio.get("events")

        if isinstance(canonical_events, list):
            return [
                event
                for event in canonical_events
                if isinstance(event, dict)
                and _event_title(event)
            ]

        # Legacy mobile_audio structure without explicit events.
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

    # Expand common TTS-hostile abbreviations.
    #
    # Use non-word boundaries here because U.S. / E.U. end in
    # punctuation, so a trailing \b does not reliably match.
    replacements = [
        (r"(?<![A-Za-z])U\.S\.(?![A-Za-z])", "United States"),
        (r"(?<![A-Za-z])U\.K\.(?![A-Za-z])", "United Kingdom"),
        (r"(?<![A-Za-z])U\.N\.(?![A-Za-z])", "United Nations"),
        (r"(?<![A-Za-z])E\.U\.(?![A-Za-z])", "European Union"),
        (r"(?<![A-Za-z])EU(?![A-Za-z])", "European Union"),
        (r"(?<![A-Za-z])UK(?![A-Za-z])", "United Kingdom"),
        (r"(?<![A-Za-z])DR Congo(?![A-Za-z])", "Democratic Republic of the Congo"),
        (r"(?<![A-Za-z])AI(?![A-Za-z])", "A I"),
        (r"(?<![A-Za-z0-9])G20(?![A-Za-z0-9])", "G twenty"),
        (r"(?<![A-Za-z0-9])G7(?![A-Za-z0-9])", "G seven"),
        (r"\bUAVs\b", "U A V's"),
    ]

    for pattern, replacement in replacements:
        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE,
        )

    # Normalize euro amounts for natural speech.
    text = re.sub(
        r"€\s*(\d+(?:\.\d+)?)\s*(billion|million|trillion)?",
        lambda match: (
            f"{match.group(1)} "
            f"{match.group(2) + ' ' if match.group(2) else ''}"
            "euros"
        ),
        text,
        flags=re.IGNORECASE,
    )

    # Speak common calendar years naturally instead of as
    # comma-separated integers such as "2,026".
    def _spoken_year(match: re.Match[str]) -> str:
        year = int(match.group(0))

        if 2000 <= year <= 2099:
            last_two = year % 100

            if last_two == 0:
                return "two thousand"

            if last_two < 10:
                return f"twenty oh {last_two}"

            number_words = {
                10: "ten",
                11: "eleven",
                12: "twelve",
                13: "thirteen",
                14: "fourteen",
                15: "fifteen",
                16: "sixteen",
                17: "seventeen",
                18: "eighteen",
                19: "nineteen",
                20: "twenty",
                21: "twenty-one",
                22: "twenty-two",
                23: "twenty-three",
                24: "twenty-four",
                25: "twenty-five",
                26: "twenty-six",
                27: "twenty-seven",
                28: "twenty-eight",
                29: "twenty-nine",
                30: "thirty",
                31: "thirty-one",
                32: "thirty-two",
                33: "thirty-three",
                34: "thirty-four",
                35: "thirty-five",
                36: "thirty-six",
                37: "thirty-seven",
                38: "thirty-eight",
                39: "thirty-nine",
                40: "forty",
                41: "forty-one",
                42: "forty-two",
                43: "forty-three",
                44: "forty-four",
                45: "forty-five",
                46: "forty-six",
                47: "forty-seven",
                48: "forty-eight",
                49: "forty-nine",
                50: "fifty",
                51: "fifty-one",
                52: "fifty-two",
                53: "fifty-three",
                54: "fifty-four",
                55: "fifty-five",
                56: "fifty-six",
                57: "fifty-seven",
                58: "fifty-eight",
                59: "fifty-nine",
                60: "sixty",
                61: "sixty-one",
                62: "sixty-two",
                63: "sixty-three",
                64: "sixty-four",
                65: "sixty-five",
                66: "sixty-six",
                67: "sixty-seven",
                68: "sixty-eight",
                69: "sixty-nine",
                70: "seventy",
                71: "seventy-one",
                72: "seventy-two",
                73: "seventy-three",
                74: "seventy-four",
                75: "seventy-five",
                76: "seventy-six",
                77: "seventy-seven",
                78: "seventy-eight",
                79: "seventy-nine",
                80: "eighty",
                81: "eighty-one",
                82: "eighty-two",
                83: "eighty-three",
                84: "eighty-four",
                85: "eighty-five",
                86: "eighty-six",
                87: "eighty-seven",
                88: "eighty-eight",
                89: "eighty-nine",
                90: "ninety",
                91: "ninety-one",
                92: "ninety-two",
                93: "ninety-three",
                94: "ninety-four",
                95: "ninety-five",
                96: "ninety-six",
                97: "ninety-seven",
                98: "ninety-eight",
                99: "ninety-nine",
            }

            return f"twenty {number_words[last_two]}"

        if 1900 <= year <= 1999:
            last_two = year % 100

            if last_two == 0:
                return "nineteen hundred"

            if last_two < 10:
                return f"nineteen oh {last_two}"

            number_words = {
                10: "ten",
                11: "eleven",
                12: "twelve",
                13: "thirteen",
                14: "fourteen",
                15: "fifteen",
                16: "sixteen",
                17: "seventeen",
                18: "eighteen",
                19: "nineteen",
                20: "twenty",
                21: "twenty-one",
                22: "twenty-two",
                23: "twenty-three",
                24: "twenty-four",
                25: "twenty-five",
                26: "twenty-six",
                27: "twenty-seven",
                28: "twenty-eight",
                29: "twenty-nine",
                30: "thirty",
                31: "thirty-one",
                32: "thirty-two",
                33: "thirty-three",
                34: "thirty-four",
                35: "thirty-five",
                36: "thirty-six",
                37: "thirty-seven",
                38: "thirty-eight",
                39: "thirty-nine",
                40: "forty",
                41: "forty-one",
                42: "forty-two",
                43: "forty-three",
                44: "forty-four",
                45: "forty-five",
                46: "forty-six",
                47: "forty-seven",
                48: "forty-eight",
                49: "forty-nine",
                50: "fifty",
                51: "fifty-one",
                52: "fifty-two",
                53: "fifty-three",
                54: "fifty-four",
                55: "fifty-five",
                56: "fifty-six",
                57: "fifty-seven",
                58: "fifty-eight",
                59: "fifty-nine",
                60: "sixty",
                61: "sixty-one",
                62: "sixty-two",
                63: "sixty-three",
                64: "sixty-four",
                65: "sixty-five",
                66: "sixty-six",
                67: "sixty-seven",
                68: "sixty-eight",
                69: "sixty-nine",
                70: "seventy",
                71: "seventy-one",
                72: "seventy-two",
                73: "seventy-three",
                74: "seventy-four",
                75: "seventy-five",
                76: "seventy-six",
                77: "seventy-seven",
                78: "seventy-eight",
                79: "seventy-nine",
                80: "eighty",
                81: "eighty-one",
                82: "eighty-two",
                83: "eighty-three",
                84: "eighty-four",
                85: "eighty-five",
                86: "eighty-six",
                87: "eighty-seven",
                88: "eighty-eight",
                89: "eighty-nine",
                90: "ninety",
                91: "ninety-one",
                92: "ninety-two",
                93: "ninety-three",
                94: "ninety-four",
                95: "ninety-five",
                96: "ninety-six",
                97: "ninety-seven",
                98: "ninety-eight",
                99: "ninety-nine",
            }

            return f"nineteen {number_words[last_two]}"

        return match.group(0)


    text = re.sub(
        r"(?<![A-Za-z0-9])(?:19|20)\d{2}(?![A-Za-z0-9])",
        _spoken_year,
        text,
    )

    # Fix common source-normalization artifacts.
    text = re.sub(
        r"\bdont\b",
        "don't",
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


def _remove_title_overlap(title: str, summary: str) -> str:
    """
    Remove a leading summary fragment that substantially repeats
    the headline.

    The comparison is based on normalized content words. The
    summary is cut only when its leading content-word run strongly
    overlaps the headline and enough new information remains.
    """

    if not title or not summary:
        return summary

    stopwords = {
        "a", "an", "the", "and", "or", "but", "to", "of", "in",
        "on", "for", "from", "by", "with", "at", "as", "is", "are",
        "was", "were", "be", "been", "being", "this", "that",
        "these", "those", "ahead", "among", "into", "after",
        "before", "than", "their", "its", "his", "her", "our",
        "your", "they", "them",
    }

    def stem(word: str) -> str:
        value = word.lower()

        for suffix in (
            "ingly",
            "edly",
            "ing",
            "ed",
            "ions",
            "ion",
            "ies",
            "es",
            "s",
        ):
            if (
                len(value) > len(suffix) + 3
                and value.endswith(suffix)
            ):
                value = value[:-len(suffix)]
                break

        return value

    def content_tokens(text: str) -> list[str]:
        words = re.findall(r"[A-Za-z]+", text.lower())
        return [
            stem(word)
            for word in words
            if word not in stopwords
        ]

    title_tokens = content_tokens(title)

    if len(title_tokens) < 3:
        return summary

    title_set = set(title_tokens)

    summary_words = summary.split()

    # Map every original summary word to its normalized content token.
    normalized_words: list[tuple[int, str]] = []

    for index, word in enumerate(summary_words):
        tokens = re.findall(r"[A-Za-z]+", word.lower())

        for token in tokens:
            if token not in stopwords:
                normalized_words.append(
                    (index, stem(token))
                )

    if not normalized_words:
        return summary

    # Look only at the leading run. We do not want to remove
    # legitimate later references to the headline topic.
    matched_positions: list[int] = []
    seen_non_title = 0

    for token_position, (word_index, token) in enumerate(
        normalized_words
    ):
        if token in title_set:
            matched_positions.append(word_index)
        else:
            seen_non_title += 1

        # Once two genuinely new content words appear at the
        # beginning, the headline overlap has ended.
        if seen_non_title >= 2:
            break

    if len(matched_positions) < 3:
        return summary

    matched_unique = len(
        {
            normalized_words[pos][1]
            for pos, (_, token) in enumerate(normalized_words)
            if pos < len(matched_positions)
            and token in title_set
        }
    )

    coverage = matched_unique / len(title_set)

    if coverage < 0.65:
        return summary

    # Cut after the LAST original word belonging to the initial
    # overlapping run, so trailing headline words such as "Usmanov"
    # are not left behind.
    last_overlap_word_index = max(matched_positions)

    remainder = " ".join(
        summary_words[last_overlap_word_index + 1:]
    ).strip(" ,;:-")

    if len(remainder.split()) < 6:
        return summary

    return remainder

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

    number_words = {
        1: "ONE",
        2: "TWO",
        3: "THREE",
        4: "FOUR",
        5: "FIVE",
        6: "SIX",
        7: "SEVEN",
        8: "EIGHT",
        9: "NINE",
        10: "TEN",
        11: "ELEVEN",
        12: "TWELVE",
        13: "THIRTEEN",
        14: "FOURTEEN",
        15: "FIFTEEN",
        16: "SIXTEEN",
        17: "SEVENTEEN",
        18: "EIGHTEEN",
        19: "NINETEEN",
        20: "TWENTY",
        21: "TWENTY-ONE",
        22: "TWENTY-TWO",
        23: "TWENTY-THREE",
        24: "TWENTY-FOUR",
        25: "TWENTY-FIVE",
        26: "TWENTY-SIX",
        27: "TWENTY-SEVEN",
        28: "TWENTY-EIGHT",
        29: "TWENTY-NINE",
        30: "THIRTY",
        31: "THIRTY-ONE",
        32: "THIRTY-TWO",
        33: "THIRTY-THREE",
        34: "THIRTY-FOUR",
        35: "THIRTY-FIVE",
        36: "THIRTY-SIX",
        37: "THIRTY-SEVEN",
        38: "THIRTY-EIGHT",
        39: "THIRTY-NINE",
        40: "FORTY",
        41: "FORTY-ONE",
        42: "FORTY-TWO",
        43: "FORTY-THREE",
        44: "FORTY-FOUR",
        45: "FORTY-FIVE",
        46: "FORTY-SIX",
        47: "FORTY-SEVEN",
        48: "FORTY-EIGHT",
        49: "FORTY-NINE",
        50: "FIFTY",
        51: "FIFTY-ONE",
        52: "FIFTY-TWO",
        53: "FIFTY-THREE",
        54: "FIFTY-FOUR",
        55: "FIFTY-FIVE",
        56: "FIFTY-SIX",
        57: "FIFTY-SEVEN",
        58: "FIFTY-EIGHT",
        59: "FIFTY-NINE",
        60: "SIXTY",
        61: "SIXTY-ONE",
        62: "SIXTY-TWO",
        63: "SIXTY-THREE",
        64: "SIXTY-FOUR",
        65: "SIXTY-FIVE",
        66: "SIXTY-SIX",
        67: "SIXTY-SEVEN",
        68: "SIXTY-EIGHT",
        69: "SIXTY-NINE",
        70: "SEVENTY",
        71: "SEVENTY-ONE",
        72: "SEVENTY-TWO",
        73: "SEVENTY-THREE",
        74: "SEVENTY-FOUR",
        75: "SEVENTY-FIVE",
        76: "SEVENTY-SIX",
        77: "SEVENTY-SEVEN",
        78: "SEVENTY-EIGHT",
        79: "SEVENTY-NINE",
        80: "EIGHTY",
        81: "EIGHTY-ONE",
        82: "EIGHTY-TWO",
        83: "EIGHTY-THREE",
        84: "EIGHTY-FOUR",
        85: "EIGHTY-FIVE",
        86: "EIGHTY-SIX",
        87: "EIGHTY-SEVEN",
        88: "EIGHTY-EIGHT",
        89: "EIGHTY-NINE",
        90: "NINETY",
        91: "NINETY-ONE",
        92: "NINETY-TWO",
        93: "NINETY-THREE",
        94: "NINETY-FOUR",
        95: "NINETY-FIVE",
        96: "NINETY-SIX",
        97: "NINETY-SEVEN",
        98: "NINETY-EIGHT",
        99: "NINETY-NINE",
    }

    for index, event in enumerate(
        production_events,
        start=1,
    ):
        title = _spoken_title(
            _event_title(event)
        )

        raw_summary = _event_summary(event)

        raw_summary = _remove_title_overlap(
            title,
            raw_summary,
        )

        summary = _spoken_summary(
            raw_summary
        )

        source = _spoken_source(
            _event_source(event)
        )

        if not title:
            continue

        lines.append(
            number_words.get(
                index,
                str(index),
            ) + "."
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
