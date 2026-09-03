from pipeline.audio_script import build_audio_script


def test_audio_script_is_deterministic():
    edition = {
        "edition_label": "EDITION 0001",
        "events": [
            {
                "title": "World headline",
                "summary": "World summary",
            },
        ],
    }

    result = build_audio_script(edition)

    assert result == (
        "EDITION 0001\n\n"
        "1. World headline\n\n"
        "World summary"
    )


def test_audio_script_ignores_invalid_events():
    edition = {
        "edition_label": "EDITION 0001",
        "events": [None, {}, {"title": "Valid"}],
    }

    result = build_audio_script(edition)

    assert "Valid" in result
    assert "None" not in result
