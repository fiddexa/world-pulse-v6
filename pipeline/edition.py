"""
AROUND THE MAIN v6 - Edition Builder

Builds a deterministic editorial edition from processed events.

This layer does not generate or rewrite news.
It only decides how already-processed events should be
organized into an edition.
"""
import re

from typing import Any

from pipeline.edition_id import build_edition_id


SECTION_ORDER = (
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
)


ROLE_ORDER = (
    "LEAD_STORY",
    "TOP_STORY",
    "SECTION_STORY",
    "MAIN_STORY",
    "BRIEF",
)


def _safe_number(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0


def _editorial(event: dict) -> dict:
    value = event.get("editorial")

    if isinstance(value, dict):
        return value

    return {}


def _score(event: dict) -> float:
    editorial = _editorial(event)

    return _safe_number(
        editorial.get(
            "ranking_score",
            event.get("ranking_score", 0.0),
        )
    )


def _role(event: dict) -> str:
    editorial = _editorial(event)

    role = editorial.get("role")

    if role:
        value = str(role).strip().upper()

        aliases = {
            "FRONT_PAGE": "LEAD_STORY",
            "LEAD_STORY": "LEAD_STORY",
            "TOP_STORY": "TOP_STORY",
            "IMPORTANT": "SECTION_STORY",
            "SECTION_STORY": "SECTION_STORY",
            "MAIN_STORY": "MAIN_STORY",
            "STANDARD": "BRIEF",
            "BRIEF": "BRIEF",
        }

        return aliases.get(value, value)

    return "BRIEF"

def _section(event: dict) -> str:
    """
    Determine the primary edition section.

    Existing event/category information is preferred.
    Unknown categories fall back to 'world'.
    """

    category = event.get("category")

    if category:
        value = str(category).strip().lower()

        aliases = {
            "world": "world",
            "international": "world",
            "politics": "geopolitics",
            "political": "geopolitics",
            "geopolitics": "geopolitics",
            "security": "geopolitics",
            "business": "business",
            "finance": "business",
            "economy": "business",
            "economic": "business",
            "energy": "energy",
            "oil": "energy",
            "gas": "energy",
            "technology": "technology",
            "tech": "technology",
            "ai": "technology",
            "science": "science_health",
            "health": "science_health",
            "medical": "science_health",
            "climate": "climate",
            "environment": "climate",
            "trade": "trade_logistics",
            "logistics": "trade_logistics",
            "society": "society",
            "culture": "culture",
            "sports": "sports",
            "sport": "sports",
        }

        return aliases.get(value, "world")

    return "world"


def _is_publishable(event: dict) -> bool:
    if not isinstance(event, dict):
        return False

    editorial = _editorial(event)

    decision = str(
        editorial.get("decision", "STANDARD")
    ).strip().upper()

    return decision not in {
        "REJECT",
        "EXCLUDE",
        "HOLD",
    }


def _decision(event: dict) -> str:
    editorial = _editorial(event)

    return str(
        editorial.get(
            "decision",
            "",
        )
    ).strip().upper()


def _sort_key(event: dict) -> tuple:
    role = _role(event)
    decision = _decision(event)

    try:
        role_index = ROLE_ORDER.index(role)
    except ValueError:
        role_index = len(ROLE_ORDER)

    decision_order = {
        "FRONT_PAGE": 0,
        "TOP_STORY": 1,
        "IMPORTANT": 2,
        "STANDARD": 3,
        "IGNORE": 4,
    }

    decision_index = decision_order.get(
        decision,
        len(decision_order),
    )

    return (
        role_index,
        decision_index,
        -_score(event),
    )


MOBILE_AUDIO_TOTAL = 30
MOBILE_AUDIO_MIN_FILL = 25
MOBILE_AUDIO_TOP = 1
MOBILE_AUDIO_SECTION = 23
MOBILE_AUDIO_BRIEFS = 6
MOBILE_AUDIO_MIN_SCORE = 32.0
MOBILE_AUDIO_MAX_PER_SECTION = 5
MOBILE_AUDIO_MAX_PER_COUNTRY = 3


def _build_mobile_audio_selection(events: list[dict]) -> dict:
    """
    Build the broad Mobile/Audio feed from the common Edition Model.

    Rules:
    - target up to 30 stories
    - keep at least 25 when the candidate pool allows it
    - score threshold >= 32
    - exclude explicitly unconfirmed events
    - exclude obvious bulletin/roundup/meta headlines
    - diversify sections and countries
    - never select two stories from the same country on the same broad topic
    """

    generic_regions = {
        "global", "world", "europe", "asia", "africa", "americas",
        "north_america", "south_america", "middle_east",
        "central_asia", "southeast_asia", "east_asia", "south_asia",
    }

    country_names = {
        "afghanistan", "albania", "algeria", "angola", "argentina", "armenia",
        "australia", "austria", "azerbaijan", "bahrain", "bangladesh",
        "belarus", "belgium", "belize", "benin", "bhutan", "bolivia",
        "bosnia_and_herzegovina", "botswana", "brazil", "brunei",
        "bulgaria", "burkina_faso", "burundi", "cambodia", "cameroon",
        "canada", "chad", "chile", "china", "colombia", "comoros",
        "congo", "costa_rica", "croatia", "cuba", "cyprus", "czechia",
        "denmark", "djibouti", "dominican_republic", "ecuador", "egypt",
        "el_salvador", "eritrea", "estonia", "ethiopia", "finland",
        "france", "gabon", "gambia", "georgia", "germany", "ghana",
        "greece", "guatemala", "guinea", "guyana", "haiti", "honduras",
        "hungary", "iceland", "india", "indonesia", "iran", "iraq",
        "ireland", "israel", "italy", "ivory_coast", "jamaica", "japan",
        "jordan", "kazakhstan", "kenya", "kuwait", "kyrgyzstan", "laos",
        "latvia", "lebanon", "lesotho", "liberia", "libya", "lithuania",
        "luxembourg", "madagascar", "malawi", "malaysia", "maldives",
        "mali", "malta", "mauritania", "mauritius", "mexico", "moldova",
        "mongolia", "montenegro", "morocco", "mozambique", "myanmar",
        "namibia", "nepal", "netherlands", "new_zealand", "nicaragua",
        "niger", "nigeria", "north_korea", "north_macedonia", "norway",
        "oman", "pakistan", "panama", "paraguay", "peru", "philippines",
        "poland", "portugal", "qatar", "romania", "russia", "rwanda",
        "saudi_arabia", "senegal", "serbia", "singapore", "slovakia",
        "slovenia", "somalia", "south_africa", "south_korea", "south_sudan",
        "spain", "sri_lanka", "sudan", "sweden", "switzerland", "syria",
        "taiwan", "tajikistan", "tanzania", "thailand", "togo", "tunisia",
        "turkey", "turkmenistan", "uganda", "ukraine",
        "united_arab_emirates", "united_kingdom", "united_states",
        "uruguay", "uzbekistan", "venezuela", "vietnam", "yemen",
        "zambia", "zimbabwe", "palestine", "kosovo",
    }

    topic_groups = {
        "conflict": {
            "military_conflict", "military", "attack", "drone_attack",
            "missile_strike", "bombing", "explosion", "casualty",
            "terrorism", "security",
        },
        "politics": {
            "political", "diplomatic", "election", "government",
            "policy", "leadership",
        },
        "economy": {
            "economic", "business", "investment", "funding", "finance",
            "trade",
        },
        "energy": {"energy", "oil", "gas", "electricity"},
        "technology": {
            "technology", "cyber", "ai", "artificial_intelligence", "space",
        },
        "health": {
            "health", "disease", "pandemic", "outbreak", "medical",
        },
        "climate": {
            "climate", "flood", "earthquake", "wildfire",
            "natural_disaster", "disaster",
        },
        "society": {
            "humanitarian", "education", "migration", "society",
            "culture", "protest",
        },
        "sports": {"sports"},
    }

    roundup_re = re.compile(
        r"\b("
        r"latest\s+news\s+bulletin|news\s+bulletin|"
        r"daily\s+roundup|morning\s+roundup|evening\s+roundup|"
        r"morning\s+briefing|evening\s+briefing|"
        r"news\s+roundup|what\s+you\s+need\s+to\s+know|"
        r"explainer|explained|"
        r"why\s+it\s+matters|"
        r"history\s+of|"
        r"connection\s+to|"
        r"what\s+is|"
        r"how\s+it\s+works"
        r")\b",
        re.IGNORECASE,
    )

    def text_of(event):
        content = event.get("content") or {}
        return str(
            content.get("headline")
            or event.get("headline")
            or event.get("title")
            or ""
        ).strip()

    def section_of(event):
        content = event.get("content") or {}
        return str(
            content.get("section")
            or event.get("section")
            or "world"
        ).strip().lower() or "world"

    def locations_of(event):
        content = event.get("content") or {}
        values = list(content.get("affected_areas") or [])

        for article in event.get("articles") or []:
            values.extend(article.get("locations") or [])

        values.extend(event.get("locations") or [])

        result = set()

        for value in values:
            token = (
                str(value).strip().lower()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if token and token not in generic_regions:
                result.add(token)

        return result

    country_headline_aliases = {
        "american": "united_states",
        "british": "united_kingdom",
        "canadian": "canada",
        "chinese": "china",
        "french": "france",
        "german": "germany",
        "greek": "greece",
        "indian": "india",
        "indonesian": "indonesia",
        "iranian": "iran",
        "iraqi": "iraq",
        "israeli": "israel",
        "italian": "italy",
        "japanese": "japan",
        "kenyan": "kenya",
        "lebanese": "lebanon",
        "libyan": "libya",
        "malaysian": "malaysia",
        "moldovan": "moldova",
        "nepali": "nepal",
        "nigerian": "nigeria",
        "norwegian": "norway",
        "pakistani": "pakistan",
        "polish": "poland",
        "portuguese": "portugal",
        "qatari": "qatar",
        "russian": "russia",
        "saudi": "saudi_arabia",
        "senegalese": "senegal",
        "serbian": "serbia",
        "south_korean": "south_korea",
        "spanish": "spain",
        "sudanese": "sudan",
        "syrian": "syria",
        "taiwanese": "taiwan",
        "thai": "thailand",
        "turkish": "turkey",
        "ukrainian": "ukraine",
        "uzbek": "uzbekistan",
        "vietnamese": "vietnam",
        "yemeni": "yemen",
        "zambian": "zambia",
        "zimbabwean": "zimbabwe",
        "malian": "mali",
        "egyptian": "egypt",
        "ethiopian": "ethiopia",
        "ghanaian": "ghana",
        "jordanian": "jordan",
        "moroccan": "morocco",
        "nepalese": "nepal",
        "filipino": "philippines",
        "philippine": "philippines",
        "congolese": "democratic_republic_of_congo",
    }

    def countries_of(event):
        countries = {
            token
            for token in locations_of(event)
            if token in country_names
        }

        title = text_of(event).lower()

        for country in country_names:
            phrase = country.replace("_", " ")
            if re.search(r"\b" + re.escape(phrase) + r"\b", title):
                countries.add(country)

        for alias, country in country_headline_aliases.items():
            if re.search(r"\b" + re.escape(alias) + r"\b", title):
                countries.add(country)

        return countries

    def topic_of(event):
        # The Edition Model section is the primary editorial topic.
        # Event types are used only as a fallback when the section is
        # missing or too generic.
        section = section_of(event)

        section_map = {
            "world": "world",
            "geopolitics": "politics",
            "business": "economy",
            "energy": "energy",
            "technology": "technology",
            "science_health": "health",
            "climate": "climate",
            "trade_logistics": "economy",
            "society": "society",
            "culture": "society",
            "sports": "sports",
        }

        mapped_section = section_map.get(section)

        if mapped_section and mapped_section != "world":
            return mapped_section

        content = event.get("content") or {}
        values = list(content.get("event_types") or [])

        for article in event.get("articles") or []:
            values.extend(article.get("event_types") or [])

        event_types = {
            str(value).strip().lower()
            .replace("-", "_")
            .replace(" ", "_")
            for value in values
        }

        # Ordered fallback: choose the broadest meaningful topic.
        for family in (
            "conflict",
            "politics",
            "economy",
            "energy",
            "technology",
            "health",
            "climate",
            "society",
            "sports",
        ):
            if event_types & topic_groups[family]:
                return family

        return "world"

    def event_key(event):
        urls = sorted(
            str(article.get("url") or "").strip()
            for article in event.get("articles") or []
            if article.get("url")
        )

        if urls:
            return urls[0]

        return re.sub(r"\s+", " ", text_of(event)).lower()[:240]

    candidates = []

    for event in events:
        if not isinstance(event, dict):
            continue

        if _score(event) < MOBILE_AUDIO_MIN_SCORE:
            continue

        verification = (
            event.get("verification") or {}
        ).get("verification_level", "")

        if str(verification).upper() == "UNCONFIRMED":
            continue

        title = text_of(event)

        if not title:
            continue

        if roundup_re.search(title):
            continue

        candidates.append(event)

    candidates.sort(
        key=lambda event: (
            _score(event),
            (event.get("content") or {}).get("freshness_score", 0),
        ),
        reverse=True,
    )

    selected = []
    selected_keys = set()
    country_topic_seen = set()
    section_counts = {}
    country_counts = {}

    def diversity_value(event):
        section = section_of(event)
        countries = countries_of(event)

        value = _score(event)

        if section not in section_counts:
            value += 10.0
        elif section_counts[section] < MOBILE_AUDIO_MAX_PER_SECTION:
            value += 1.5
        else:
            value -= 12.0

        # Avoid allowing geopolitics to dominate the feed when
        # several other editorial sections still have candidates.
        if section == "geopolitics":
            geo_count = section_counts.get("geopolitics", 0)

            if geo_count >= 6:
                value -= 7.0

            if geo_count >= 8:
                value -= 12.0

        if countries:
            if any(country not in country_counts for country in countries):
                value += 6.0
            else:
                value -= 3.0

            if any(
                country_counts.get(country, 0) >= MOBILE_AUDIO_MAX_PER_COUNTRY
                for country in countries
            ):
                value -= 5.0

        return value

    while len(selected) < MOBILE_AUDIO_TOTAL:
        available = []

        for event in candidates:
            key = event_key(event)

            if key in selected_keys:
                continue

            countries = countries_of(event)
            topic = topic_of(event)

            if countries and any(
                (country, topic) in country_topic_seen
                for country in countries
            ):
                continue

            available.append(event)

        if not available:
            break

        best = max(available, key=diversity_value)

        selected.append(best)
        selected_keys.add(event_key(best))

        section = section_of(best)
        section_counts[section] = section_counts.get(section, 0) + 1

        countries = countries_of(best)
        topic = topic_of(best)

        for country in countries:
            country_counts[country] = country_counts.get(country, 0) + 1
            country_topic_seen.add((country, topic))

    top_story = selected[0] if selected else None
    main_end = min(
        len(selected),
        MOBILE_AUDIO_TOP + MOBILE_AUDIO_SECTION,
    )

    return {
        "top_story": top_story,
        "main_stories": selected[MOBILE_AUDIO_TOP:main_end],
        "briefs": selected[main_end:MOBILE_AUDIO_TOTAL],
        "events": selected,
        "event_count": len(selected),
        "candidate_count": len(candidates),
    }


def build_edition(
    events: Any,
    publication_date=None,
    edition_time=None,
    *,
    exclude_ignored: bool = False,
) -> dict:
    """
    Build one deterministic edition structure.

    No external services, AI APIs, or network calls are used.
    """

    if not isinstance(events, list):
        events = []

    publishable = [
        event
        for event in events
        if isinstance(event, dict)
        and _is_publishable(event)
        and not (
            exclude_ignored
            and str(
                _editorial(event).get(
                    "decision",
                    "",
                )
            ).strip().upper() == "IGNORE"
        )
    ]

    ordered = sorted(
        publishable,
        key=_sort_key,
    )

    top_story = None
    main_stories = []
    briefs = []

    for event in ordered:
        role = _role(event)

        if role == "LEAD_STORY" and top_story is None:
            top_story = event
        elif role == "TOP_STORY" and top_story is None:
            top_story = event
        elif role in {
            "SECTION_STORY",
            "MAIN_STORY",
        }:
            main_stories.append(event)
        else:
            briefs.append(event)

    sections = {
        section: []
        for section in SECTION_ORDER
    }

    for event in ordered:
        section = _section(event)

        sections.setdefault(
            section,
            [],
        ).append(event)

    mobile_audio = _build_mobile_audio_selection(
        ordered,
    )

    result = {
        "edition_type": "WORLD_PULSE",
        "event_count": len(ordered),
        "ordered": ordered,
        "top_story": top_story,
        "main_stories": main_stories,
        "briefs": briefs,
        "sections": sections,
        "mobile_audio": mobile_audio,
    }

    if publication_date is not None and edition_time is not None:
        result["edition_id"] = build_edition_id(
            publication_date,
            edition_time,
        )

    return result


def build_editions(
    events: Any,
    publication_date=None,
    edition_time=None,
) -> list[dict]:
    """
    Convenience wrapper for future multi-edition support.
    """

    return [
        build_edition(
            events,
            publication_date=publication_date,
            edition_time=edition_time,
        )
    ]
