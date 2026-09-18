"""Shared geographic helpers for AROUND THE MAIN."""

import re


GENERIC_REGIONS = {
    "global", "world", "europe", "asia", "africa", "americas",
    "north_america", "south_america", "middle_east",
    "central_asia", "southeast_asia", "east_asia", "south_asia",
}


COUNTRY_NAMES = {
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


COUNTRY_HEADLINE_ALIASES = {
    "american": "united_states",
    "americans": "united_states",
    "british": "united_kingdom",
    "canadian": "canada",
    "canadians": "canada",
    "australian": "australia",
    "australians": "australia",
    "israeli": "israel",
    "israelis": "israel",
    "nigerian": "nigeria",
    "nigerians": "nigeria",
    "south african": "south_africa",
    "south africans": "south_africa",
    "chinese": "china",
    "french": "france",
    "german": "germany",
    "greek": "greece",
    "indian": "india",
    "indonesian": "indonesia",
    "iranian": "iran",
    "iraqi": "iraq",
    "italian": "italy",
    "japanese": "japan",
    "kenyan": "kenya",
    "lebanese": "lebanon",
    "libyan": "libya",
    "malaysian": "malaysia",
    "moldovan": "moldova",
    "nepali": "nepal",
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


HEADLINE_PLACE_ALIASES = {
    "greenland": "greenland",
    "antarctica": "antarctica",
    "dubai": "united_arab_emirates",
    "lisbon": "portugal",
    "barcelona": "spain",
    "ceuta": "spain",
    "san francisco": "united_states",
    "madrid": "spain",
    "zagreb": "croatia",
}


HEADLINE_REGION_ALIASES = {
    "europe": "europe",
    "european": "europe",
    "europeans": "europe",
    "asia": "asia",
    "asian": "asia",
    "asians": "asia",
    "africa": "africa",
    "african": "africa",
    "africans": "africa",
    "americas": "americas",
    "north america": "north_america",
    "north american": "north_america",
    "north americans": "north_america",
    "south america": "south_america",
    "south american": "south_america",
    "south americans": "south_america",
    "middle east": "middle_east",
    "middle eastern": "middle_east",
    "central asia": "central_asia",
    "southeast asia": "southeast_asia",
    "east asia": "east_asia",
    "south asia": "south_asia",
}


def detect_headline_countries(title):
    """Return canonical countries mentioned in a headline, in text order."""

    if not title:
        return []

    raw_text = str(title).strip()
    text = raw_text.lower()
    matches = []

    for country in COUNTRY_NAMES:
        phrase = country.replace("_", " ")
        match = re.search(
            r"\b" + re.escape(phrase) + r"\b",
            text,
        )
        if match:
            matches.append(
                (match.start(), -len(phrase), country)
            )

    for alias, country in COUNTRY_HEADLINE_ALIASES.items():
        phrase = alias.replace("_", " ")
        match = re.search(
            r"\b" + re.escape(phrase) + r"\b",
            text,
        )
        if match:
            matches.append(
                (match.start(), -len(phrase), country)
            )


    # Detect only explicit uppercase US/U.S. abbreviations.
    for match in re.finditer(
        r"(?<![A-Za-z])(?:US|U\.S\.)(?![A-Za-z])",
        raw_text,
    ):
        matches.append(
            (
                match.start(),
                -len(match.group(0)),
                "united_states",
            )
        )
    matches.sort()

    result = []

    for _, _, country in matches:
        if country not in result:
            result.append(country)

    return result


def detect_headline_places(title):
    """Return canonical places mentioned in a headline, in text order."""

    if not title:
        return []

    text = str(title).strip().lower()
    matches = []

    for alias, place in HEADLINE_PLACE_ALIASES.items():
        match = re.search(
            r"\b" + re.escape(alias) + r"\b",
            text,
        )

        if match:
            matches.append(
                (match.start(), -len(alias), place)
            )

    matches.sort()

    result = []

    for _, _, place in matches:
        if place not in result:
            result.append(place)

    return result


def detect_headline_regions(title):
    """Return canonical broad regions mentioned in a headline, in text order."""

    if not title:
        return []

    text = str(title).strip().lower()
    matches = []

    for alias, region in HEADLINE_REGION_ALIASES.items():
        match = re.search(
            r"\b" + re.escape(alias) + r"\b",
            text,
        )

        if match:
            matches.append(
                (match.start(), -len(alias), region)
            )

    matches.sort()

    result = []

    for _, _, region in matches:
        if region not in result:
            result.append(region)

    return result


def countries_from_event_locations(values):
    """Return country identifiers from existing event location metadata."""

    if not values:
        return set()

    result = set()

    for value in values:
        token = (
            str(value).strip().lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if token and token not in GENERIC_REGIONS:
            if token in COUNTRY_NAMES:
                result.add(token)

    return result
