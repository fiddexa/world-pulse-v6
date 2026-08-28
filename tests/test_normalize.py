from pipeline.normalize import (
    normalize_text,
    normalize_source,
    normalize_article,
)


def test_normalize_text():
    assert normalize_text(
        "  Ukraine — STRIKE!  "
    ) == "ukraine - strike"


def test_normalize_unicode():
    assert normalize_text(
        "Россия — Украина"
    ) == "россия - украина"


def test_normalize_source():
    assert normalize_source(
        "  Reuters  "
    ) == "reuters"


def test_normalize_article():

    article = {
        "title": "  Major Earthquake!  ",
        "summary": "  Emergency response begins. ",
        "source": " Reuters ",
        "category": " Natural Disaster ",
        "region": " Asia ",
    }

    result = normalize_article(
        article
    )

    assert result["title"] == "major earthquake"
    assert result["summary"] == "emergency response begins"
    assert result["source"] == "reuters"
    assert result["category"] == "natural disaster"
    assert result["region"] == "asia"


def test_invalid_article():
    assert normalize_article(None) == {}
    assert normalize_article("text") == {}
