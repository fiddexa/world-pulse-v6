"""
WORLD PULSE v6 - Intelligence Layer

Measures objective event impact.

This layer is independent from:
- verification
- editorial ranking
"""


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

    articles = event.get("articles")

    if not isinstance(articles, list):
        return []

    return [
        article
        for article in articles
        if isinstance(article, dict)
    ]


def _event_types(event):
    values = set()

    if not isinstance(event, dict):
        return values

    direct = event.get("event_types")

    for value in _safe_list(direct):
        if value:
            values.add(str(value).strip().lower())

    for article in _articles(event):
        value = article.get("event_types")

        for item in _safe_list(value):
            if item:
                values.add(str(item).strip().lower())

    return values


def _locations(event):
    values = set()

    if not isinstance(event, dict):
        return values

    direct = event.get("locations")

    for value in _safe_list(direct):
        if value:
            values.add(str(value).strip().lower())

    for article in _articles(event):
        value = article.get("locations")

        for item in _safe_list(value):
            if item:
                values.add(str(item).strip().lower())

    return values


def _max_casualty_number(event):
    if not isinstance(event, dict):
        return 0.0

    maximum = 0.0

    direct = event.get("casualty_numbers")

    for value in _safe_list(direct):
        number = _safe_number(value)

        if number is not None:
            maximum = max(maximum, number)

    casualty_keys = (
        "casualty_numbers",
        "casualties",
        "death_toll",
        "deaths",
        "killed",
        "injured",
        "wounded",
    )

    for article in _articles(event):
        for key in casualty_keys:
            for value in _safe_list(article.get(key)):
                number = _safe_number(value)

                if number is not None:
                    maximum = max(maximum, number)

    return maximum


def _casualty_score(event):
    number = _max_casualty_number(event)

    if number <= 0:
        return 0.0

    if number == 1:
        return 8.0

    if number <= 5:
        return 12.0

    if number <= 10:
        return 16.0

    if number <= 25:
        return 22.0

    if number <= 50:
        return 27.0

    if number <= 100:
        return 31.0

    if number <= 500:
        return 35.0

    return 40.0


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
}


MEDIUM_IMPACT_TYPES = {
    "political",
    "diplomatic",
    "economic",
    "legislation",
    "protest",
    "election",
}


def _type_score(event):
    types = _event_types(event)

    if not types:
        return 0.0

    if types & HIGH_IMPACT_TYPES:
        return 30.0

    if types & MEDIUM_IMPACT_TYPES:
        return 18.0

    return 8.0


def _geographic_score(event):
    count = len(_locations(event))

    if count <= 0:
        return 0.0

    if count == 1:
        return 5.0

    if count == 2:
        return 9.0

    if count == 3:
        return 12.0

    return 15.0


def _scope_score(event):
    count = len(_articles(event))

    if count <= 1:
        return 0.0

    if count == 2:
        return 3.0
    if count == 3:
        return 4.0

    return 5.0


def intelligence_score(event):
    """
    Return objective event-impact score from 0 to 100.

    Verification data is intentionally ignored.
    """

    if not isinstance(event, dict):
        return 0.0

    score = (
        _type_score(event)
        + _casualty_score(event)
        + _geographic_score(event)
        + _scope_score(event)
    )

    return round(
        max(0.0, min(100.0, score)),
        2,
    )


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
    score = intelligence_score(event)

    return {
        "score": score,
        "level": intelligence_level(score),
        "event_types": sorted(_event_types(event)),
        "locations": sorted(_locations(event)),
        "maximum_casualty_number": _max_casualty_number(event),
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
