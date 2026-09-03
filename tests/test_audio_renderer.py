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
