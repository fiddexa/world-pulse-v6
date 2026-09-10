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

    Editorial classification is based primarily on the event headline,
    summary and short article metadata. Full article bodies are not used
    for section classification because secondary keywords can distort the
    primary topic.

    Countries and locations alone never determine the section.
    """

    allowed = {
        "world",
        "geopolitics",
        "business",
        "energy",
        "technology",
        "science_health",
        "climate",
        "trade_logistics",
        "society",
        "culture",
        "sports",
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
        value = _first_nonempty(editorial.get("section"))

        if value:
            normalized = aliases.get(value.strip().lower())

            if normalized in allowed and normalized != "world":
                return normalized

    headline_parts = []
    context_parts = []

    def add_headline(value):
        value = _first_nonempty(value)
        if value:
            headline_parts.append(value)

    def add_context(value):
        value = _first_nonempty(value)
        if value:
            context_parts.append(value)

    add_headline(event.get("title"))
    add_headline(event.get("headline"))

    add_context(event.get("summary"))
    add_context(event.get("description"))
    add_context(event.get("why_it_matters"))

    for article in _articles(event):
        if not isinstance(article, dict):
            continue

        add_headline(article.get("title"))
        add_headline(article.get("headline"))

        add_context(article.get("summary"))
        add_context(article.get("description"))

    headline = " ".join(headline_parts).lower()
    context = " ".join(context_parts).lower()
    text = f"{headline} {context}"

    def has_any(value, keywords):
        return any(keyword in value for keyword in keywords)

    # 1. High-confidence health signals.
    if has_any(
        text,
        (
            "mpox", "monkeypox", "ebola", "outbreak", "epidemic",
            "pandemic", "virus", "disease", "vaccine", "vaccination",
            "hospital", "clinical trial", "medical", "healthcare",
            "cancer",
        ),
    ):
        return "science_health"

    # 2. High-confidence climate and environmental disasters.
    if has_any(
        text,
        (
            "climate change", "global warming", "climate",
            "flood", "flooding", "wildfire", "wildfires",
            "drought", "hurricane", "cyclone", "earthquake",
            "tsunami", "volcanic", "extreme weather",
            "heatwave", "heat wave", "emissions",
            "greenhouse gas", "deforestation",
        ),
    ):
        return "climate"

    # 3. Clear technology stories. "Information war + AI" belongs here.
    if has_any(
        text,
        (
            "artificial intelligence", "ai model", "generative ai",
            "openai", "chatgpt", "software", "semiconductor",
            "chip", "chips", "cyber", "cybersecurity",
            "cyber attack", "hackers", "hacking", "robotics",
            "robot", "smartphone", "internet", "data center",
            "space technology",
        ),
    ):
        return "technology"

    # 4. Clear culture and sports.
    if has_any(
        text,
        (
            "film", "movie", "cinema", "music", "concert",
            "museum", "theatre", "theater", "artist", "festival",
            "book", "literature", "actor", "actress",
        ),
    ):
        return "culture"

    if has_any(
        text,
        (
            "football", "soccer", "basketball", "tennis",
            "cricket", "rugby", "baseball", "hockey",
            "olympics", "olympic", "championship",
            "tournament", "league", "athlete", "athletes",
            "match", "world cup", "grand slam",
        ),
    ):
        return "sports"

    # 5. Education and civilian incidents are normally Society.
    # This is checked before the generic military/geopolitical layer.
    if has_any(
        text,
        (
            "education", "school", "schools", "classroom",
            "teacher", "teachers", "student", "students",
            "university", "universities",
            "train collides", "train collision",
            "road accident", "car crash", "truck crash",
            "plane crash", "ship fire", "ferry fire",
            "fire breaks out", "building fire",
            "wedding fire", "collision", "accident", "crash",
            "missing",
        ),
    ):
        # Exception: explicit military attacks remain geopolitical.
        if not has_any(
            headline,
            (
                "airstrike", "missile strike", "missile attack",
                "drone attack", "drone strike", "bombing",
                "military strike", "troops attack",
            ),
        ):
            return "society"

    # 6. Energy.
    if has_any(
        text,
        (
            "lng", "lpg", "crude oil", "oil price", "oil hits",
            "petroleum", "refinery", "fuel", "diesel",
            "gasoline", "jet fuel", "opec", "natural gas",
            "energy prices", "power grid", "electricity",
            "solar power", "wind power", "nuclear power",
            "energy",
        ),
    ):
        return "energy"

    # 7. Trade/logistics.
    if has_any(
        text,
        (
            "imports", "import", "exports", "export",
            "tariff", "tariffs", "customs", "shipping",
            "shipment", "logistics", "cargo", "freight",
            "supply chain", "trade agreement", "trade deal",
            "trade restrictions", "ban imports",
        ),
    ):
        return "trade_logistics"

    # 8. Business/economics.
    if has_any(
        text,
        (
            "budget deficit", "investment", "invests",
            "investors", "company", "companies", "corporate",
            "corporation", "market", "markets", "stock",
            "stocks", "shares", "finance", "financial",
            "economy", "economic", "gdp", "inflation",
            "interest rate", "earnings", "profit",
            "merger", "acquisition", "funding",
        ),
    ):
        return "business"

    # 9. Geopolitics: strong political / diplomatic / military signals.
    # Country names alone are deliberately NOT included.
    if has_any(
        text,
        (
            "war", "conflict", "military", "army", "troops",
            "missile", "missiles", "airstrike", "drone attack",
            "drone strike", "drone war", "bombing",
            "weapons depot", "weapons", "ceasefire",
            "peace talks", "peace negotiations",
            "de-escalation", "diplomatic", "diplomacy",
            "sanctions", "foreign policy",
            "president", "prime minister", "foreign minister",
            "lawmakers", "parliament", "election", "elections",
            "midterm", "midterms", "government",
            "summit", "arms deal", "military hardware",
            "chemical weapons", "intelligence warned",
        ),
    ):
        return "geopolitics"

    # 10. General society fallback.
    if has_any(
        text,
        (
            "society", "social", "population", "migration",
            "migrant", "refugee", "protest", "protests",
            "demonstration", "demonstrations",
            "crime", "police", "workers", "labor", "labour",
            "humanitarian",
        ),
    ):
        return "society"

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
