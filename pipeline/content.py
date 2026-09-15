"""
AROUND THE MAIN v6 - Content Builder

Builds publication-ready structured content from editorial events.

This layer:
- does not invent facts;
- does not change verification;
- does not change intelligence;
- does not change ranking;
- preserves the original event.
"""


def _safe_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return []


def _articles(event):
    if not isinstance(event, dict):
        return []

    return [
        article
        for article in _safe_list(event.get("articles"))
        if isinstance(article, dict)
    ]


def _first_nonempty(*values):
    for value in values:
        if value is None:
            continue

        text = str(value).strip()

        if text:
            return text

    return ""


def _headline(event):
    articles = _articles(event)

    for article in articles:
        title = _first_nonempty(article.get("original_title"), article.get("title"))

        if title:
            return title

    return _first_nonempty(event.get("title"))


def _summary(event):
    articles = _articles(event)

    for article in articles:
        summary = _first_nonempty(article.get("original_summary"), article.get("summary"))

        if summary:
            return summary

    return _first_nonempty(event.get("summary"))


def _why_it_matters(event):
    """
    Return an explicitly supplied editorial context.

    This field must not be inferred from an impact score or
    generated as an unsupported opinion. If no factual/editorial
    context is supplied by an upstream layer, return an empty
    string and leave the item for editorial review.
    """

    if not isinstance(event, dict):
        return ""

    content = event.get("content")

    if isinstance(content, dict):
        value = _first_nonempty(
            content.get("why_it_matters")
        )

        if value:
            return value

    value = _first_nonempty(
        event.get("why_it_matters")
    )

    if value:
        return value

    for article in _articles(event):
        value = _first_nonempty(
            article.get("why_it_matters")
        )

        if value:
            return value

    return ""


def _section(event):
    editorial = event.get("editorial")

    if isinstance(editorial, dict):
        section = _first_nonempty(editorial.get("section"))

        if section:
            return section

    categories = []

    for article in _articles(event):
        category = _first_nonempty(article.get("category"))

        if category and category not in categories:
            categories.append(category)

    if categories:
        return categories[0]

    return "world"


def _sources(event):
    verification = event.get("verification")

    if isinstance(verification, dict):
        sources = _safe_list(verification.get("sources"))

        cleaned = []

        for source in sources:
            value = _first_nonempty(source)

            if value and value not in cleaned:
                cleaned.append(value)

        if cleaned:
            return cleaned

    sources = []

    for article in _articles(event):
        source = _first_nonempty(article.get("source"))

        if source and source not in sources:
            sources.append(source)

    return sources


def _published_at(event):
    articles = _articles(event)

    for article in articles:
        value = _first_nonempty(article.get("published_at"))

        if value:
            return value

    return _first_nonempty(event.get("published_at"))


def _verification_status(event):
    verification = event.get("verification")

    if not isinstance(verification, dict):
        return "UNCONFIRMED"

    return _first_nonempty(
        verification.get("verification_level"),
        "UNCONFIRMED",
    )


def _locations(event):
    intelligence = event.get("intelligence")

    if isinstance(intelligence, dict):
        locations = _safe_list(intelligence.get("locations"))

        cleaned = [
            _first_nonempty(value)
            for value in locations
            if _first_nonempty(value)
        ]

        if cleaned:
            return cleaned

    locations = []

    for article in _articles(event):
        for value in _safe_list(article.get("locations")):
            value = _first_nonempty(value)

            if value and value not in locations:
                locations.append(value)

    return locations


def build_content(event):
    """
    Add deterministic publication content metadata.

    The original event is never modified.
    """

    if not isinstance(event, dict):
        return {}

    result = dict(event)

    result["content"] = {
        "headline": _headline(event),
        "summary": _summary(event),
        "why_it_matters": _why_it_matters(event),
        "section": _section(event),
        "verification": _verification_status(event),
        "sources": _sources(event),
        "published_at": _published_at(event),
        "affected_areas": _locations(event),
    }

    return result


def build_contents(events):
    """
    Build content metadata for a list of events.
    """

    if not isinstance(events, list):
        return []

    return [
        build_content(event)
        for event in events
        if isinstance(event, dict)
    ]
