"""
AROUND THE MAIN v6 - Global Impact Layer

Measures objective event impact for editorial ranking.

This layer does not determine truth and does not replace verification.
It evaluates the practical significance of an event for an international
news audience.
"""

import re


def _safe_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return []


def _safe_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _articles(event):
    if not isinstance(event, dict):
        return []

    value = event.get("articles")

    if not isinstance(value, list):
        return []

    return [
        article
        for article in value
        if isinstance(article, dict)
    ]


def _text(event):
    parts = []

    if isinstance(event, dict):
        for key in (
            "title",
            "headline",
            "summary",
            "description",
            "what_happened",
            "category",
        ):
            value = event.get(key)
            if value:
                parts.append(str(value))

        content = event.get("content")
        if isinstance(content, dict):
            for key in (
                "headline",
                "summary",
                "what_happened",
            ):
                value = content.get(key)
                if value:
                    parts.append(str(value))

    for article in _articles(event):
        for key in (
            "title",
            "headline",
            "summary",
            "description",
        ):
            value = article.get(key)
            if value:
                parts.append(str(value))

    return " ".join(parts).strip().lower()


def _event_types(event):
    values = set()

    if not isinstance(event, dict):
        return values

    for value in _safe_list(event.get("event_types")):
        if value:
            values.add(str(value).strip().lower())

    for article in _articles(event):
        for value in _safe_list(article.get("event_types")):
            if value:
                values.add(str(value).strip().lower())

    return values


def _locations(event):
    values = set()

    if not isinstance(event, dict):
        return values

    for value in _safe_list(event.get("locations")):
        if value:
            values.add(str(value).strip().lower())

    for article in _articles(event):
        for value in _safe_list(article.get("locations")):
            if value:
                values.add(str(value).strip().lower())

    return values


def _max_casualty_number(event):
    maximum = 0.0

    if not isinstance(event, dict):
        return maximum

    direct_values = _safe_list(event.get("casualty_numbers"))

    for value in direct_values:
        number = _safe_number(value)
        if number is not None:
            maximum = max(maximum, number)

    keys = (
        "casualty_numbers",
        "casualties",
        "death_toll",
        "deaths",
        "killed",
        "injured",
        "wounded",
    )

    for article in _articles(event):
        for key in keys:
            for value in _safe_list(article.get(key)):
                number = _safe_number(value)
                if number is not None:
                    maximum = max(maximum, number)

    return maximum


def _scale_numbers(event):
    results = []

    if not isinstance(event, dict):
        return results

    direct = event.get("scale_numbers")

    if isinstance(direct, list):
        results.extend(
            item for item in direct
            if isinstance(item, dict)
        )

    for article in _articles(event):
        values = article.get("scale_numbers")

        if isinstance(values, list):
            results.extend(
                item for item in values
                if isinstance(item, dict)
            )

    return results


def _maximum_scale_number(event):
    maximum = 0.0

    for item in _scale_numbers(event):
        value = _safe_number(item.get("value"))
        multiplier = _safe_number(item.get("multiplier"))

        if value is None or multiplier is None or multiplier <= 0:
            continue

        maximum = max(maximum, value * multiplier)

    return maximum


def _scale_score(event):
    number = _maximum_scale_number(event)

    if number < 1_000:
        return 0.0
    if number < 10_000:
        return 8.0
    if number < 100_000:
        return 16.0
    if number < 500_000:
        return 24.0
    if number < 1_000_000:
        return 30.0
    if number < 5_000_000:
        return 38.0
    return 45.0


def _casualty_score(event):
    number = _max_casualty_number(event)

    if number <= 0:
        return 0.0
    if number == 1:
        return 8.0
    if number <= 5:
        return 14.0
    if number <= 10:
        return 20.0
    if number <= 25:
        return 27.0
    if number <= 50:
        return 34.0
    if number <= 100:
        return 40.0
    if number <= 500:
        return 47.0
    return 55.0


HIGH_IMPACT_TYPES = {
    "military_conflict",
    "attack",
    "missile_strike",
    "airstrike",
    "drone_attack",
    "bombing",
    "explosion",
    "earthquake",
    "tsunami",
    "volcano",
    "hurricane",
    "flood",
    "wildfire",
    "disease",
    "humanitarian",
    "death",
    "casualty",
}


MEDIUM_IMPACT_TYPES = {
    "political",
    "diplomatic",
    "economic",
    "legislation",
    "protest",
    "election",
    "security",
    "health",
    "environmental",
}


def _type_score(event):
    types = _event_types(event)

    if types & HIGH_IMPACT_TYPES:
        return 40.0

    if types & MEDIUM_IMPACT_TYPES:
        return 24.0

    text = _text(event)

    high_signal = (
        "war",
        "missile",
        "airstrike",
        "attack",
        "invasion",
        "ceasefire",
        "conflict",
        "earthquake",
        "flood",
        "wildfire",
        "outbreak",
        "epidemic",
        "pandemic",
        "evacuation",
    )

    medium_signal = (
        "election",
        "president",
        "government",
        "sanctions",
        "diplomatic",
        "summit",
        "trade",
        "economy",
        "energy",
        "climate",
        "health",
    )

    if any(term in text for term in high_signal):
        return 34.0

    if any(term in text for term in medium_signal):
        return 20.0

    return 8.0


def _geographic_score(event):
    locations = _locations(event)
    count = len(locations)

    if count == 0:
        return 4.0
    if count == 1:
        return 10.0
    if count == 2:
        return 18.0
    if count == 3:
        return 24.0

    return 30.0


def _international_reach_score(event):
    text = _text(event)
    locations = _locations(event)

    score = min(20.0, len(locations) * 4.0)

    international_signals = (
        "international",
        "global",
        "worldwide",
        "cross-border",
        "regional",
        "united nations",
        "security council",
        "g20",
        "g7",
        "sco",
        "nato",
        "european union",
    )

    if any(term in text for term in international_signals):
        score += 8.0

    return min(30.0, score)


def _strategic_score(event):
    text = _text(event)
    types = _event_types(event)

    score = 0.0

    strategic_types = {
        "military_conflict",
        "attack",
        "political",
        "diplomatic",
        "economic",
        "election",
        "security",
        "energy",
    }

    if types & strategic_types:
        score += 16.0

    strategic_terms = (
        "sanctions",
        "ceasefire",
        "peace talks",
        "nuclear",
        "security council",
        "oil",
        "gas",
        "energy supply",
        "trade agreement",
        "tariff",
        "presidential election",
        "prime minister",
    )

    if any(term in text for term in strategic_terms):
        score += 10.0

    return min(30.0, score)


def _scope_score(event):
    count = len(_articles(event))

    if count <= 1:
        return 0.0
    if count == 2:
        return 5.0
    if count == 3:
        return 8.0
    return 12.0


def global_impact_score(event):
    """
    Objective global-impact estimate from 0 to 100.
    """

    if not isinstance(event, dict):
        return 0.0

    score = (
        _type_score(event)
        + _casualty_score(event) * 0.55
        + _scale_score(event) * 0.60
        + _geographic_score(event) * 0.45
        + _international_reach_score(event) * 0.55
        + _strategic_score(event) * 0.65
        + _scope_score(event)
    )

    return round(
        max(0.0, min(100.0, score)),
        2,
    )


def intelligence_score(event):
    """
    Backward-compatible name used by the current pipeline.
    """

    return global_impact_score(event)


def intelligence_level(score):
    value = _safe_number(score)

    if value is None:
        value = 0.0

    if value >= 80:
        return "CRITICAL"
    if value >= 65:
        return "VERY_HIGH"
    if value >= 50:
        return "HIGH"
    if value >= 30:
        return "MEDIUM"

    return "LOW"


def analyze_event(event):
    score = global_impact_score(event)

    return {
        "score": score,
        "level": intelligence_level(score),
        "global_impact_score": score,
        "event_types": sorted(_event_types(event)),
        "locations": sorted(_locations(event)),
        "maximum_casualty_number": _max_casualty_number(event),
        "maximum_scale_number": _maximum_scale_number(event),
        "scale_score": round(_scale_score(event), 2),
        "casualty_score": round(_casualty_score(event), 2),
        "international_reach_score": round(
            _international_reach_score(event),
            2,
        ),
        "strategic_score": round(
            _strategic_score(event),
            2,
        ),
        "article_count": len(_articles(event)),
    }


def analyze_events(events):
    if not isinstance(events, list):
        return []

    results = []

    for event in events:
        if not isinstance(event, dict):
            continue

        result = dict(event)
        result["intelligence"] = analyze_event(event)
        results.append(result)

    return results
