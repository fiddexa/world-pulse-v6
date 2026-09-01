from pipeline.extract import extract_facts, extract_scale_numbers


def test_ukraine_strike():

    article = {
        "title":
            "Ukrainian forces strike nuclear facility in Zaporizhzhia",

        "summary":
            "The attack damages infrastructure in Ukraine.",
    }

    facts = extract_facts(article)

    assert "military" in facts["event_types"]
    assert "ukraine" in facts["locations"]
    assert "ukraine" in facts["actors"]
    assert "infrastructure" in facts["objects"]


def test_nepal_flood():

    article = {
        "title":
            "People pulled from mud in Nepal after deadly flash floods",

        "summary":
            "At least 43 people were killed.",
    }

    facts = extract_facts(article)

    assert "natural_disaster" in facts["event_types"]
    assert "casualty" in facts["event_types"]
    assert "nepal" in facts["locations"]
    assert "43" in facts["casualty_numbers"]


def test_south_sudan():

    article = {
        "title":
            "Two UN peacekeepers killed in South Sudan ambush",
    }

    facts = extract_facts(article)

    assert "casualty" in facts["event_types"]
    assert "sudan" in facts["locations"]
    assert "un" in facts["actors"]
    assert "2" in facts["casualty_numbers"]


def test_no_false_casualty_number():

    article = {
        "title":
            "Russia announces 2026 economic plan",
    }

    facts = extract_facts(article)

    assert "2026" in facts["numbers"]
    assert facts["casualty_numbers"] == []


def test_extracts_population_scale_numbers():
    article = {
        "title":
            "One million children in Afghanistan face deadly malnutrition",
        "summary":
            "Some 3.7 million children are suffering from wasting, "
            "with around one million facing the most severe form.",
    }

    facts = extract_facts(article)

    assert "scale_numbers" in facts

    values = facts["scale_numbers"]

    assert any(
        item["value"] == 1
        and item["multiplier"] == 1_000_000
        for item in values
    )

    assert any(
        item["value"] == 3.7
        and item["multiplier"] == 1_000_000
        for item in values
    )


def test_extracts_displacement_scale():
    article = {
        "title":
            "More than 500,000 people displaced by devastating floods",
        "summary": "",
    }

    facts = extract_facts(article)

    assert "scale_numbers" in facts

    assert any(
        item["value"] == 500
        and item["multiplier"] == 1_000
        for item in facts["scale_numbers"]
    )


def test_scale_numbers_do_not_become_casualties():
    article = {
        "title":
            "One million children face severe malnutrition",
        "summary": "",
    }

    facts = extract_facts(article)

    assert facts["casualty_numbers"] == []


def test_scale_context_uses_livelihoods_when_number_describes_livelihoods():
    text = (
        "threatening the livelihoods of over three billion people"
    )

    result = extract_scale_numbers(text)

    assert result == [
        {
            "value": 3.0,
            "multiplier": 1_000_000_000,
            "raw": "three billion",
            "context": "livelihoods",
        }
    ]
def test_livelihood_context_is_detected_from_summary():
    article = {
        "title": "Land degradation threatens livelihoods",
        "summary": (
            "Threatening the livelihoods of over three billion people."
        ),
    }

    facts = extract_facts(article)

    assert facts["scale_numbers"] == [
        {
            "value": 3.0,
            "multiplier": 1_000_000_000,
            "raw": "three billion",
            "context": "livelihoods",
        }
    ]
