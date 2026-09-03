from pathlib import Path

import pytest

from pipeline.edition_audio import (
    edition_audio_filename,
    generate_edition_audio,
)


class FakeRenderer:
    def __init__(self):
        self.calls = []

    def render(self, script, output_path):
        self.calls.append((script, output_path))
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"FAKE-MP3")
        return output


def test_edition_audio_filename_uses_edition_number():
    assert (
        edition_audio_filename(
            {
                "edition_id": "2026-09-03T07:00",
                "edition_number": 47,
            }
        )
        == "EDITION_0047.mp3"
    )


def test_edition_audio_filename_pads_number():
    assert (
        edition_audio_filename(
            {
                "edition_number": 1,
            }
        )
        == "EDITION_0001.mp3"
    )


def test_edition_audio_filename_rejects_missing_number():
    with pytest.raises(ValueError):
        edition_audio_filename(
            {
                "edition_id": "2026-09-03T07:00",
            }
        )


def test_generate_edition_audio(tmp_path):
    renderer = FakeRenderer()

    edition = {
        "edition_id": "2026-09-03T07:00",
        "edition_number": 47,
        "edition_label": "EDITION 0047",
        "top_story": {
            "title": "Global markets open higher",
            "summary": "Markets rose in early trading.",
        },
        "main_stories": [],
        "briefs": [],
    }

    result = generate_edition_audio(
        edition,
        output_dir=tmp_path,
        audio_renderer=renderer,
    )

    assert result["status"] == "GENERATED"
    assert result["edition_number"] == 47
    assert result["filename"] == "EDITION_0047.mp3"

    audio = tmp_path / "EDITION_0047.mp3"

    assert audio.is_file()
    assert audio.read_bytes() == b"FAKE-MP3"
    assert renderer.calls


def test_generate_edition_audio_requires_edition_id(tmp_path):
    result = generate_edition_audio(
        {
            "edition_number": 47,
            "main_stories": [],
            "briefs": [],
        },
        output_dir=tmp_path,
        audio_renderer=FakeRenderer(),
    )

    assert result["status"] == "FAILED"
    assert result["reason"] == "MISSING_EDITION_ID"


def test_generate_edition_audio_requires_edition_number(tmp_path):
    result = generate_edition_audio(
        {
            "edition_id": "2026-09-03T07:00",
            "main_stories": [],
            "briefs": [],
        },
        output_dir=tmp_path,
        audio_renderer=FakeRenderer(),
    )

    assert result["status"] == "FAILED"
    assert result["reason"] == "MISSING_EDITION_NUMBER"
