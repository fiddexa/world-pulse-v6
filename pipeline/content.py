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
    """
    Determine the primary editorial section for an event.

    Priority:
    1. Explicit editorial section, when it matches a supported section.
    2. Deterministic content-based classification.
    3. WORLD fallback.

    A country/location is never used as the section.
    """

    allowed = {
        "world": "world",
        "geopolitics": "geopolitics",
        "business": "business",
        "energy": "energy",
        "technology": "technology",
        "science_health": "science_health",
        "climate": "climate",
        "trade_logistics": "trade_logistics",
        "society": "society",
        "culture": "culture",
        "sports": "sports",
    }

    aliases = {
        "world": "world",
        "geopolitics": "geopolitics",
        "politics": "geopolitics",
        "business": "business",
        "economy": "business",
        "economic": "business",
        "energy": "energy",
        "technology": "technology",
        "tech": "technology",
        "science": "science_health",
        "health": "science_health",
        "science_health": "science_health",
        "science & health": "science_health",
        "climate": "climate",
        "environment": "climate",
        "trade": "trade_logistics",
        "logistics": "trade_logistics",
        "trade_logistics": "trade_logistics",
        "society": "society",
        "social": "society",
        "culture": "culture",
        "arts": "culture",
        "sports": "sports",
        "sport": "sports",
    }

    editorial = event.get("editorial")

    if isinstance(editorial, dict):
        value = _first_nonempty(
            editorial.get("section")
        )

        if value:
            normalized = aliases.get(
                value.strip().lower()
            )

            # Trust explicit editorial categories,
            # but let generic WORLD be classified from content.
            if normalized in allowed.values() and normalized != "world":
                return normalized

    parts = []

    def add_text(value):
        value = _first_nonempty(value)

        if value:
            parts.append(value)

    add_text(event.get("title"))
    add_text(event.get("headline"))
    add_text(event.get("summary"))
    add_text(event.get("description"))
    add_text(event.get("why_it_matters"))

    for article in _articles(event):
        if not isinstance(article, dict):
            continue

        add_text(article.get("title"))
        add_text(article.get("headline"))
        add_text(article.get("summary"))
        add_text(article.get("description"))
        add_text(article.get("content"))

    text = " ".join(parts).lower()

    rules = {
        "climate": (
            "climate", "climate change", "global warming",
            "flood", "flooding", "wildfire", "wildfires",
            "drought", "hurricane", "cyclone", "storm",
            "earthquake", "tsunami", "volcanic",
            "extreme weather", "heatwave", "heat wave",
            "environment", "emissions", "carbon",
            "greenhouse gas", "deforestation",
        ),

        "energy": (
            "oil", "crude", "petroleum", "gas", "natural gas",
            "lng", "lpg", "opec", "opec+", "refinery",
            "refinery", "fuel", "diesel", "gasoline",
            "jet fuel", "electricity", "power grid",
            "energy", "solar power", "wind power",
            "nuclear power",
        ),

        "technology": (
            "technology", "tech", "artificial intelligence",
            "ai model", "ai", "software", "semiconductor",
            "chip", "chips", "computer", "cyber",
            "cybersecurity", "robot", "robotics",
            "smartphone", "internet", "data center",
            "space technology",
        ),

        "sports": (
            "football", "soccer", "basketball", "tennis",
            "cricket", "rugby", "baseball", "hockey",
            "olympics", "olympic", "championship",
            "tournament", "league", "athlete", "athletes",
            "match", "world cup", "grand slam",
        ),

        "culture": (
            "film", "movie", "cinema", "music", "concert",
            "museum", "theatre", "theater", "art",
            "artist", "culture", "cultural", "festival",
            "book", "literature", "actor", "actress",
        ),

        "science_health": (
            "health", "medical", "medicine", "hospital",
            "doctor", "disease", "virus", "vaccine",
            "vaccination", "pandemic", "epidemic",
            "who ", "unicef", "cancer", "clinical trial",
            "research", "scientists", "science", "study",
            "drug", "healthcare",
        ),

        "trade_logistics": (
            "trade", "trading", "export", "exports",
            "import", "imports", "tariff", "tariffs",
            "customs", "shipping", "shipment",
            "logistics", "port", "ports", "cargo",
            "freight", "supply chain", "supply chains",
            "trade agreement", "trade deal",
        ),

        "business": (
            "business", "company", "companies", "corporate",
            "corporation", "market", "markets", "stock",
            "stocks", "shares", "investor", "investors",
            "investment", "bank", "banking", "finance",
            "financial", "economy", "economic", "gdp",
            "inflation", "interest rate", "earnings",
            "profit", "merger", "acquisition",
        ),

        "society": (
            "election", "elections", "government", "protest",
            "protests", "demonstration", "demonstrations",
            "society", "social", "population", "migration",
            "migrant", "refugee", "refugees", "education",
            "school", "schools", "crime", "police",
            "workers", "labor", "labour",
        ),

        "geopolitics": (
            "war", "conflict", "military", "army",
            "troops", "missile", "missiles", "nato",
            "sanctions", "diplomatic", "diplomacy",
            "president", "prime minister", "foreign minister",
            "summit", "peace talks", "ceasefire",
            "iran", "israel", "ukraine", "russia",
            "china", "united states", "north korea",
        ),
    }

    scores = {
        section: sum(
            1 for keyword in keywords
            if keyword in text
        )
        for section, keywords in rules.items()
    }

    best_section = max(
        scores,
        key=scores.get,
    )

    if scores[best_section] > 0:
        return best_section

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
