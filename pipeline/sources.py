"""
WORLD PULSE v6 - Source Registry

Central registry and reputation model for information sources.

The registry is intentionally independent from:
- collection
- verification
- intelligence
- ranking
- editorial selection
"""


SOURCE_TIERS = {
    "PRIMARY": 1,
    "MAJOR_MEDIA": 2,
    "SPECIALIZED": 3,
    "REGIONAL": 4,
}


SOURCE_TYPES = {
    "government",
    "central_bank",
    "international_organization",
    "company",
    "exchange",
    "regulator",
    "scientific_organization",
    "major_media",
    "specialized_media",
    "regional_media",
    "other",
}


DEFAULT_SOURCE = {
    "tier": 4,
    "source_type": "other",
    "region": "global",
    "categories": [],
    "reputation_score": 0.0,
    "independence_score": 0.0,
    "primary_source": False,
    "active": True,
}


SOURCE_REGISTRY = {
    "reuters": {
        "name": "Reuters",
        "domain": "reuters.com",
        "tier": 2,
        "source_type": "major_media",
        "region": "global",
        "categories": [
            "world",
            "politics",
            "geopolitics",
            "security",
            "economy",
            "markets",
            "energy",
            "trade",
            "technology",
        ],
        "reputation_score": 9.5,
        "independence_score": 9.0,
        "primary_source": False,
        "active": True,
    },
    "associated_press": {
        "name": "Associated Press",
        "domain": "apnews.com",
        "tier": 2,
        "source_type": "major_media",
        "region": "global",
        "categories": [
            "world",
            "politics",
            "security",
            "economy",
            "technology",
            "climate",
            "health",
            "science",
        ],
        "reputation_score": 9.4,
        "independence_score": 9.0,
        "primary_source": False,
        "active": True,
    },
    "bbc": {
        "name": "BBC",
        "domain": "bbc.com",
        "tier": 2,
        "source_type": "major_media",
        "region": "global",
        "categories": [
            "world",
            "politics",
            "geopolitics",
            "security",
            "economy",
            "technology",
            "climate",
            "health",
            "science",
            "culture",
            "sports",
        ],
        "reputation_score": 9.2,
        "independence_score": 8.5,
        "primary_source": False,
        "active": True,
    },
    "afp": {
        "name": "Agence France-Presse",
        "domain": "afp.com",
        "tier": 2,
        "source_type": "major_media",
        "region": "global",
        "categories": [
            "world",
            "politics",
            "geopolitics",
            "security",
            "economy",
            "climate",
            "science",
        ],
        "reputation_score": 9.2,
        "independence_score": 8.5,
        "primary_source": False,
        "active": True,
    },
    "un": {
        "name": "United Nations",
        "domain": "un.org",
        "tier": 1,
        "source_type": "international_organization",
        "region": "global",
        "categories": [
            "world",
            "politics",
            "geopolitics",
            "security",
            "humanitarian",
            "climate",
            "health",
        ],
        "reputation_score": 9.8,
        "independence_score": 9.5,
        "primary_source": True,
        "active": True,
    },
    "imf": {
        "name": "International Monetary Fund",
        "domain": "imf.org",
        "tier": 1,
        "source_type": "international_organization",
        "region": "global",
        "categories": [
            "economy",
            "markets",
            "finance",
            "currencies",
],
        "reputation_score": 9.8,
        "independence_score": 9.5,
        "primary_source": True,
        "active": True,
    },
    "world_bank": {
        "name": "World Bank",
        "domain": "worldbank.org",
        "tier": 1,
        "source_type": "international_organization",
        "region": "global",
        "categories": [
            "economy",
            "development",
            "climate",
            "food",
            "water",
        ],
        "reputation_score": 9.7,
        "independence_score": 9.4,
        "primary_source": True,
        "active": True,
    },
    "who": {
        "name": "World Health Organization",
        "domain": "who.int",
        "tier": 1,
        "source_type": "international_organization",
        "region": "global",
        "categories": [
            "health",
            "science",
            "pandemic",
        ],
        "reputation_score": 9.7,
        "independence_score": 9.3,
        "primary_source": True,
        "active": True,
    },
    "iea": {
        "name": "International Energy Agency",
        "domain": "iea.org",
        "tier": 1,
        "source_type": "international_organization",
        "region": "global",
        "categories": [
            "energy",
            "oil",
            "gas",
            "electricity",
            "climate",
        ],
        "reputation_score": 9.7,
        "independence_score": 9.2,
        "primary_source": True,
        "active": True,
    },
    "opec": {
        "name": "OPEC",
        "domain": "opec.org",
        "tier": 1,
        "source_type": "international_organization",
        "region": "global",
        "categories": [
            "energy",
            "oil",
        ],
        "reputation_score": 9.5,
        "independence_score": 8.0,
        "primary_source": True,
        "active": True,
    },
}


def normalize_source_name(value):
    """
    Normalize a source name for registry lookup.
    """
    if value is None:
        return ""

    return " ".join(
        str(value).strip().lower().split()
    )


def _copy_source(source):
    """
    Return a defensive copy of a source record.
    """
    result = dict(source)

    categories = result.get("categories", [])

    if isinstance(categories, list):
        result["categories"] = list(categories)
    else:
        result["categories"] = []

    return result


def get_source(source):
    """
    Return a registered source.

    Unknown sources receive a conservative default profile.
    """
    key = normalize_source_name(source)

    if not key:
        return _copy_source(DEFAULT_SOURCE)

    if key in SOURCE_REGISTRY:
        return _copy_source(
            SOURCE_REGISTRY[key]
        )

    for record in SOURCE_REGISTRY.values():
        if normalize_source_name(
            record.get("name", "")
        ) == key:
            return _copy_source(record)

        if normalize_source_name(
            record.get("domain", "")
        ) == key:
            return _copy_source(record)

    return _copy_source(DEFAULT_SOURCE)


def source_exists(source):
    """
    Return True when the source is registered.
    """
    key = normalize_source_name(source)

    if not key:
        return False

    if key in SOURCE_REGISTRY:
        return True

    for record in SOURCE_REGISTRY.values():
        if normalize_source_name(
            record.get("name", "")
        ) == key:
            return True

        if normalize_source_name(
            record.get("domain", "")
        ) == key:
            return True

    return False


def source_reputation(source):
    """
    Return reputation score from 0 to 10.
    """
    record = get_source(source)

    try:
        value = float(
            record.get(
                "reputation_score",
                0.0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0.0

    return max(
        0.0,
        min(10.0, value),
    )
def source_independence(source):
    """
    Return independence score from 0 to 10.
    """
    record = get_source(source)

    try:
        value = float(
            record.get(
                "independence_score",
                0.0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0.0

    return max(
        0.0,
        min(10.0, value),
    )


def source_tier(source):
    """
    Return numeric source tier.

    Unknown sources conservatively receive Tier 4.
    """
    record = get_source(source)

    value = record.get("tier", 4)

    try:
        value = int(value)
    except (
        TypeError,
        ValueError,
    ):
        return 4

    return max(1, min(4, value))


def is_primary_source(source):
    """
    Return True when the source is a primary source.
    """
    record = get_source(source)

    return bool(
        record.get(
            "primary_source",
            False,
        )
    )


def source_categories(source):
    """
    Return supported categories for a source.
    """
    record = get_source(source)

    categories = record.get(
        "categories",
        [],
    )

    if not isinstance(categories, list):
        return []

    return list(categories)


def source_supports_category(
    source,
    category,
):
    """
    Return True when a source is explicitly associated
    with a category.
    """
    category_key = normalize_source_name(
        category
    )

    if not category_key:
        return False

    return category_key in {
        normalize_source_name(value)
        for value in source_categories(source)
    }


def source_profile(source):
    """
    Return the complete normalized source profile.
    """
    record = get_source(source)

    record["reputation_score"] = source_reputation(
        source
    )

    record["independence_score"] = source_independence(
        source
    )

    record["tier"] = source_tier(source)

    record["primary_source"] = is_primary_source(
        source
    )

    return record


def list_sources():
    """
    Return all registered sources as defensive copies.
    """
    return [
        _copy_source(record)
        for record in SOURCE_REGISTRY.values()
    ]
