from pipeline.extract import extract_facts


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
