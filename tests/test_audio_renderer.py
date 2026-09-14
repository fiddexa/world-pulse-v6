from pathlib import Path

import pytest

from pipeline.audio_renderer import (
    OpenAITTSRenderer,
    PiperTTSRenderer,
    StubAudioRenderer,
)


def test_stub_audio_renderer(tmp_path):
    output = tmp_path / "audio.mp3"

    result = StubAudioRenderer().render(
        "AROUND THE MAIN",
        output,
    )

    assert result == output
    assert output.is_file()
    assert output.read_bytes().startswith(
        b"AROUND-THE-MAIN-AUDIO-STUB"
    )


def test_stub_rejects_empty_script(tmp_path):
    with pytest.raises(ValueError):
        StubAudioRenderer().render(
            "",
            tmp_path / "audio.mp3",
        )


def test_openai_renderer_requires_api_key(tmp_path):
    renderer = OpenAITTSRenderer(api_key="")

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        renderer.render(
            "Test",
            tmp_path / "audio.mp3",
        )


def test_openai_script_split():
    script = (
        "First paragraph.\n\n"
        + ("word " * 2500)
        + "\n\nLast paragraph."
    )

    chunks = OpenAITTSRenderer._split_script(script)

    assert len(chunks) > 1
    assert all(
        len(chunk) <= OpenAITTSRenderer.MAX_INPUT_CHARS
        for chunk in chunks
    )


def test_openai_renderer_writes_audio(tmp_path):
    renderer = OpenAITTSRenderer(
        api_key="test-key"
    )

    calls = []

    def fake_request(text):
        calls.append(text)
        return b"FAKE-MP3-DATA"

    renderer._request = fake_request

    output = tmp_path / "edition.mp3"

    result = renderer.render(
        "AROUND THE MAIN\n\n"
        "Today we have several important stories.",
        output,
    )

    assert result == output
    assert output.read_bytes() == b"FAKE-MP3-DATA"
    assert calls


def test_piper_renderer_validates_environment(tmp_path):
    renderer = PiperTTSRenderer(
        model_path=tmp_path / "missing.onnx",
        piper_binary=None,
        ffmpeg_binary=None,
    )

    with pytest.raises(RuntimeError):
        renderer.render(
            "Test",
            tmp_path / "audio.mp3",
        )


def test_piper_renderer_requires_mp3_output(tmp_path):
    model = tmp_path / "voice.onnx"
    model.write_bytes(b"test")

    renderer = PiperTTSRenderer(
        model_path=model,
        piper_binary="piper",
        ffmpeg_binary="ffmpeg",
    )

    with pytest.raises(ValueError):
        renderer.render(
            "Test",
            tmp_path / "audio.wav",
        )


def test_piper_number_marker_detection():
    assert PiperTTSRenderer._is_number_marker("ONE.")
    assert PiperTTSRenderer._is_number_marker("TWO.")
    assert PiperTTSRenderer._is_number_marker("THREE.")
    assert PiperTTSRenderer._is_number_marker("TWENTY-ONE.")
    assert PiperTTSRenderer._is_number_marker("NINETY-NINE.")

    assert not PiperTTSRenderer._is_number_marker("ONE")
    assert not PiperTTSRenderer._is_number_marker("1.")
    assert not PiperTTSRenderer._is_number_marker("AROUND.")


def test_piper_number_markers_are_split_from_body():
    script = """AROUND THE MAIN.

September 14, 2026.

ONE.

First title.

First summary.

TWO.

Second title.

Second summary.

THREE.

Third title.

Third summary.

That was Around the Main."""

    assert PiperTTSRenderer._split_number_markers(script) == [
        (
            "body",
            "AROUND THE MAIN.\n\n"
            "September 14, 2026.",
        ),
        ("number", "ONE"),
        (
            "body",
            "First title.\n\n"
            "First summary.",
        ),
        ("number", "TWO"),
        (
            "body",
            "Second title.\n\n"
            "Second summary.",
        ),
        ("number", "THREE"),
        (
            "body",
            "Third title.\n\n"
            "Third summary.\n\n"
            "That was Around the Main.",
        ),
    ]


def test_piper_number_emphasis_configuration():
    renderer = PiperTTSRenderer(
        model_path="voice.onnx",
        piper_binary="piper",
        ffmpeg_binary="ffmpeg",
    )

    assert renderer.number_volume == 1.35
    assert renderer.number_pause_before == 0.60
    assert renderer.number_pause_after == 0.35
    assert renderer.sentence_silence == 0.35
    assert renderer.bitrate == "128k"
