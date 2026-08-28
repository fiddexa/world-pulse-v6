"""
WORLD PULSE v6 - Ranking Layer

Combines objective intelligence with moderate verification
and editorial adjustments.

Ranking does NOT modify intelligence or verification.
"""

from copy import deepcopy


EVENT_TYPE_MULTIPLIERS = {
    "DIRECT_EVENT": 1.00,
    "CASUALTY_EVENT": 1.00,
    "MILITARY_ACTION": 1.00,
    "NATURAL_DISASTER": 1.00,
    "HUMANITARIAN_CRISIS": 1.00,
    "MAJOR_POLICY_DECISION": 1.00,
    "ECONOMIC_EVENT": 1.00,
    "SECURITY_EVENT": 1.00,
    "HEALTH_EVENT": 1.00,
    "DIPLOMATIC_EVENT": 0.98,
    "POLITICAL_EVENT": 0.97,
    "TECHNOLOGY_EVENT": 0.98,
    "BUSINESS_EVENT": 0.96,
    "SCIENCE_EVENT": 0.96,
    "POLITICAL_STATEMENT": 0.90,
    "STATEMENT": 0.90,
    "ANALYSIS": 0.82,
    "FORECAST": 0.75,
    "OPINION": 0.62,
    "OTHER": 0.90,
}


EDITORIAL_CEILINGS = {
    "DIRECT_EVENT": 100.0,
    "CASUALTY_EVENT": 100.0,
    "MILITARY_ACTION": 100.0,
    "NATURAL_DISASTER": 100.0,
    "HUMANITARIAN_CRISIS": 100.0,
    "MAJOR_POLICY_DECISION": 100.0,
    "ECONOMIC_EVENT": 100.0,
    "SECURITY_EVENT": 100.0,
    "HEALTH_EVENT": 100.0,
    "DIPLOMATIC_EVENT": 89.99,
    "POLITICAL_EVENT": 84.99,
    "TECHNOLOGY_EVENT": 84.99,
    "SCIENCE_EVENT": 79.99,
    "BUSINESS_EVENT": 79.99,
    "POLITICAL_STATEMENT": 59.99,
    "STATEMENT": 59.99,
    "ANALYSIS": 59.99,
    "FORECAST": 54.99,
    "OPINION": 49.99,
    "OTHER": 54.99,
}


def _number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _intelligence_score(event):
    intelligence = event.get("intelligence", {})

    if not isinstance(intelligence, dict):
        return 0.0

    return max(
        0.0,
        min(
            100.0,
            _number(intelligence.get("score"))
        ),
    )


def _verification(event):
    verification = event.get("verification", {})

    if not isinstance(verification, dict):
        return {}

    return verification


def _verification_adjustment(event):
    verification = _verification(event)

    sources = _int(
        verification.get("independent_sources")
    )

    agreement = _number(
        verification.get("agreement")
    )

    diversity = _number(
        verification.get("source_diversity_score")
    )

    if sources <= 0:
        source_adjustment = -4.0
    elif sources == 1:
        source_adjustment = -3.5
    elif sources == 2:
        source_adjustment = -1.5
    elif sources == 3:
        source_adjustment = 0.0
    elif sources == 4:
        source_adjustment = 1.0
    else:
        source_adjustment = 1.5

    if agreement >= 0.9:
        agreement_adjustment = 1.0
    elif agreement >= 0.8:
        agreement_adjustment = 0.5
    elif agreement >= 0.6:
        agreement_adjustment = 0.0
    elif agreement > 0:
        agreement_adjustment = -1.0
    else:
        agreement_adjustment = -1.5

    if diversity >= 8.0:
        diversity_adjustment = 0.5
    elif diversity >= 5.0:
        diversity_adjustment = 0.0
    elif diversity > 0:
        diversity_adjustment = -0.5
    else:
        diversity_adjustment = 0.0

    return max(
        -5.0,
        min(
            3.0,
            source_adjustment
            + agreement_adjustment
            + diversity_adjustment,
        ),
    )


def _event_type(event):
    value = event.get("event_type", "OTHER")

    if not value:
        return "OTHER"

    return str(value).upper().strip()


def _event_multiplier(event):
    return EVENT_TYPE_MULTIPLIERS.get(
        _event_type(event),
        0.90,
    )


def _editorial_ceiling(event):
    return EDITORIAL_CEILINGS.get(
        _event_type(event),
        54.99,
    )


def _article_adjustment(event):
    articles = event.get("articles", [])

    if not isinstance(articles, list):
        return 0.0

    count = len(articles)

    if count >= 8:
        return 0.25

    if count >= 5:
        return 0.15
    if count >= 2:
        return 0.0

    return -0.25


def calculate_ranking_score(event):
    """
    Calculate final ranking score from 0 to 100.

    Intelligence is dominant.
    Verification is a moderate adjustment.
    Article volume is deliberately tiny.
    """

    if not isinstance(event, dict):
        return 0.0

    intelligence = _intelligence_score(event)

    score = intelligence * _event_multiplier(event)

    score += _verification_adjustment(event)

    score += _article_adjustment(event)

    score = min(
        score,
        _editorial_ceiling(event),
    )

    # Verification protection.
    sources = _int(
        _verification(event).get(
            "independent_sources"
        )
    )

    if sources <= 1:
        score = min(score, 89.99)

    elif sources == 2:
        score = min(score, 89.99)

    elif sources == 3:
        score = min(score, 89.99)

    return round(
        max(0.0, min(100.0, score)),
        2,
    )


def ranking_significance(score):
    value = _number(score)

    if value >= 90:
        return "CRITICAL"

    if value >= 80:
        return "VERY HIGH"

    if value >= 65:
        return "HIGH"

    if value >= 50:
        return "MEDIUM"

    return "LOW"


def rank_events(events):
    """
    Return events sorted by final ranking score.

    The input events are not modified.
    """

    if not isinstance(events, list):
        return []

    ranked = []

    for event in events:
        if not isinstance(event, dict):
            continue

        result = deepcopy(event)

        score = calculate_ranking_score(result)

        result["ranking_score"] = score
        result["ranking_significance"] = (
            ranking_significance(score)
        )

        ranked.append(result)

    ranked.sort(
        key=lambda event: event.get(
            "ranking_score",
            0.0,
        ),
        reverse=True,
    )

    return ranked
