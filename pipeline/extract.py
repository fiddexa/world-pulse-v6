import re

from pipeline.normalize import normalize_text


EVENT_PATTERNS = {
    "military": {
        "strike", "strikes", "struck",
        "attack", "attacks", "attacked",
        "missile", "missiles",
        "airstrike", "airstrikes",
        "bombing", "bombed",
        "drone", "drones",
        "war", "fighting",
        "offensive", "invasion",
    },
    "natural_disaster": {
        "earthquake", "earthquakes",
        "flood", "floods", "flooding",
        "wildfire", "wildfires",
        "storm", "storms",
        "hurricane", "typhoon",
        "tornado", "tsunami",
        "volcano", "eruption",
    },
    "casualty": {
        "killed", "killing", "dead",
        "deaths", "died",
        "wounded", "injured",
        "casualties",
    },
    "political": {
        "election", "elections",
        "president", "minister",
        "resigned", "resignation",
        "government", "parliament",
        "vote", "voting",
    },
    "economic": {
        "bankruptcy", "bankrupt",
        "tariff", "tariffs",
        "sanctions", "sanction",
        "economy", "economic",
        "trade",
    },
    "diplomatic": {
        "agreement", "treaty",
        "ceasefire", "peace",
        "negotiation", "negotiations",
    },
    "humanitarian": {
        "refugees", "famine",
        "drought", "hunger",
        "displaced", "displacement",
        "humanitarian",
    },
}


LOCATION_ALIASES = {
    "ukraine": "ukraine",
    "ukrainian": "ukraine",
    "russia": "russia",
    "russian": "russia",
    "sudan": "sudan",
    "nepal": "nepal",
    "china": "china",
    "germany": "germany",
    "france": "france",
    "poland": "poland",
    "serbia": "serbia",
    "israel": "israel",
    "palestine": "palestine",
    "gaza": "palestine",
    "iran": "iran",
    "iraq": "iraq",
    "india": "india",
    "pakistan": "pakistan",
    "usa": "united_states",
    "america": "united_states",
    "american": "united_states",
    "uk": "united_kingdom",
    "britain": "united_kingdom",
    "british": "united_kingdom",
}


ACTOR_ALIASES = {
    "ukraine": "ukraine",
    "ukrainian": "ukraine",
    "russia": "russia",
    "russian": "russia",
    "un": "un",
    "nato": "nato",
    "israel": "israel",
    "iran": "iran",
    "china": "china",
    "india": "india",
    "north korea": "north_korea",
    "south korea": "south_korea",
    "germany": "germany",
    "france": "france",
    "poland": "poland",
}


OBJECT_GROUPS = {
    "infrastructure": {
        "infrastructure",
        "facility",
        "facilities",
        "station",
        "airport",
        "bridge",
        "road",
        "railway",
        "railways",
        "power",
        "plant",
    },
    "military": {
        "military",
        "army",
        "troops",
        "soldiers",
        "base",
        "bases",
    },
    "civilian": {
        "civilian",
        "civilians",
        "residential",
        "homes",
        "house",
        "houses",
    },
    "hospital": {
        "hospital",
        "hospitals",
        "clinic",
        "clinics",
    },
}


CASUALTY_CONTEXT = {
    "killed",
    "killing",
    "dead",
    "deaths",
    "died",
    "wounded",
    "injured",
    "casualties",
}


def tokens(text):
    return {
        token
        for token in normalize_text(text).split()
        if token
    }


def extract_event_types(text):
    word_set = tokens(text)
    found = set()

    for event_type, words in EVENT_PATTERNS.items():
        if word_set.intersection(words):
            found.add(event_type)

    return sorted(found)


def extract_locations(text):
    normalized = normalize_text(text)
    word_set = set(normalized.split())
    found = set()

    for word, location in LOCATION_ALIASES.items():
        if " " in word:
            if word in normalized:
                found.add(location)
        elif word in word_set:
            found.add(location)

    return sorted(found)
def extract_actors(text):
    normalized = normalize_text(text)
    word_set = set(normalized.split())
    found = set()

    for actor, canonical in ACTOR_ALIASES.items():
        if " " in actor:
            if actor in normalized:
                found.add(canonical)
        elif actor in word_set:
            found.add(canonical)

    return sorted(found)


def extract_objects(text):
    word_set = tokens(text)
    found = set()

    for object_type, words in OBJECT_GROUPS.items():
        if word_set.intersection(words):
            found.add(object_type)

    return sorted(found)


def extract_numbers(text):
    normalized = normalize_text(text)

    matches = re.findall(
        r"\b\d+(?:[.,]\d+)?\b",
        normalized,
    )

    return sorted(set(matches))


def extract_casualty_numbers(text):
    normalized = normalize_text(text)
    results = set()

    number_words = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
    }

    casualty_words = {
        "killed",
        "killing",
        "dead",
        "deaths",
        "died",
        "wounded",
        "injured",
        "casualties",
    }

    # -----------------------------------------------------
    # DIGIT NUMBERS
    # -----------------------------------------------------

    digit_pattern = (
        r"\b(\d+(?:[.,]\d+)?)\b"
        r"(?:\s+\w+){0,4}\s+"
        r"(?:"
        + "|".join(
            re.escape(word)
            for word in sorted(casualty_words)
        )
        + r")\b"
    )

    for match in re.finditer(
        digit_pattern,
        normalized
    ):
        results.add(match.group(1))

    # -----------------------------------------------------
    # SIMPLE NUMBER WORDS
    # -----------------------------------------------------

    word_pattern = (
        r"\b("
        + "|".join(
            re.escape(word)
            for word in sorted(
                number_words,
                key=len,
                reverse=True
            )
        )
        + r")\b"
        r"(?:\s+\w+){0,4}\s+"
        r"(?:"
        + "|".join(
            re.escape(word)
            for word in sorted(casualty_words)
        )
        + r")\b"
    )

    for match in re.finditer(
        word_pattern,
        normalized
    ):
        word = match.group(1)
        results.add(
            str(number_words[word])
        )

    # -----------------------------------------------------
    # HYPHENATED NUMBERS
    # forty-three, twenty-five, etc.
    # -----------------------------------------------------

    tens = {
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
    }

    units = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
    }

    hyphen_pattern = (
        r"\b("
        + "|".join(tens)
        + r")-("
        + "|".join(units)
        + r")\b"
        r"(?:\s+\w+){0,4}\s+"
        r"(?:"
        + "|".join(
            re.escape(word)
            for word in sorted(casualty_words)
        )
        + r")\b"
    )

    for match in re.finditer(
        hyphen_pattern,
        normalized
    ):
        value = (
            tens[match.group(1)]
            + units[match.group(2)]
        )

        results.add(
            str(value)
        )

    return sorted(results)


def extract_facts(article):
    if not isinstance(article, dict):
        return {}

    title = article.get("title", "")
    summary = article.get("summary", "")

    text = " ".join(
        part
        for part in (title, summary)
        if part
    )

    return {
        "event_types": extract_event_types(text),
        "locations": extract_locations(text),
        "actors": extract_actors(text),
        "objects": extract_objects(text),
        "numbers": extract_numbers(text),
        "casualty_numbers": extract_casualty_numbers(text),
    }
