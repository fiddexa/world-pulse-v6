"""
AROUND THE MAIN — Audio Renderer

Production audio rendering uses local Piper TTS.

Primary voice:
    en_US-ryan-medium

Fallback provider:
    OpenAITTSRenderer

The renderer interface remains provider-independent.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Protocol


class AudioRenderer(Protocol):
    def render(self, script: str, output_path: str | Path) -> Path:
        ...


class StubAudioRenderer:
    """Deterministic test renderer; never calls an external service."""

    def render(
        self,
        script: str,
        output_path: str | Path,
    ) -> Path:
        if not isinstance(script, str) or not script.strip():
            raise ValueError("script must not be empty")

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        output.write_bytes(
            b"AROUND-THE-MAIN-AUDIO-STUB\n"
            + script.encode("utf-8")
        )

        return output


class PiperTTSRenderer:
    """
    Local production TTS renderer.

    Default voice:
        en_US-ryan-medium

    The renderer creates a WAV file with Piper and converts it to MP3
    using FFmpeg.
    """

    DEFAULT_MODEL = Path(
        "tools/piper/voices/en_US-ryan-medium.onnx"
    )

    def __init__(
        self,
        *,
        model_path: str | Path | None = None,
        piper_binary: str | None = None,
        ffmpeg_binary: str | None = None,
        sentence_silence: float = 0.40,
        noise_w: float = 0.0,
        length_scale: float = 0.92,
        bitrate: str = "128k",
        timeout: int = 300,
    ) -> None:
        self.model_path = Path(
            model_path or self.DEFAULT_MODEL
        )

        self.piper_binary = (
            piper_binary
            or os.getenv("PIPER_BINARY")
            or shutil.which("piper")
        )

        self.ffmpeg_binary = (
            ffmpeg_binary
            or os.getenv("FFMPEG_BINARY")
            or shutil.which("ffmpeg")
        )

        self.sentence_silence = float(sentence_silence)
        self.noise_w = float(noise_w)
        self.length_scale = float(length_scale)
        self.bitrate = str(bitrate)
        self.timeout = int(timeout)

    def render(
        self,
        script: str,
        output_path: str | Path,
    ) -> Path:
        if not isinstance(script, str) or not script.strip():
            raise ValueError("script must not be empty")

        if not self.piper_binary:
            raise RuntimeError(
                "Piper executable not found"
            )

        if not self.ffmpeg_binary:
            raise RuntimeError(
                "FFmpeg executable not found"
            )

        if not self.model_path.is_file():
            raise RuntimeError(
                f"Piper model not found: {self.model_path}"
            )

        output = Path(output_path)

        if output.suffix.lower() != ".mp3":
            raise ValueError(
                "PiperTTSRenderer output must be an .mp3 file"
            )

        output.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(
            prefix="around-the-main-audio-"
        ) as temp_dir:
            wav_path = Path(temp_dir) / "voice.wav"

            piper_result = subprocess.run(
                [
                    self.piper_binary,
                    "--model",
                    str(self.model_path),
                    "--output_file",
                    str(wav_path),
                    "--sentence-silence",
                    str(self.sentence_silence),
                    "--noise_w",
                    str(self.noise_w),
                    "--length_scale",
                    str(self.length_scale),
                ],
                input=script,
                text=True,
                capture_output=True,
                timeout=self.timeout,
            )

            if piper_result.returncode != 0:
                raise RuntimeError(
                    "Piper failed: "
                    + (
                        piper_result.stderr.strip()
                        or piper_result.stdout.strip()
                        or "unknown error"
                    )
                )

            if not wav_path.is_file() or wav_path.stat().st_size == 0:
                raise RuntimeError(
                    "Piper did not create an audio file"
                )

            ffmpeg_result = subprocess.run(
                [
                    self.ffmpeg_binary,
                    "-y",
                    "-i",
                    str(wav_path),
                    "-codec:a",
                    "libmp3lame",
                    "-b:a",
                    self.bitrate,
                    str(output),
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if ffmpeg_result.returncode != 0:
                raise RuntimeError(
                    "FFmpeg failed: "
                    + (
                        ffmpeg_result.stderr.strip()
                        or ffmpeg_result.stdout.strip()
                        or "unknown error"
                    )
                )

        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(
                "MP3 audio file was not created"
            )

        return output


class OpenAITTSRenderer:
    """
    Fallback text-to-speech renderer using the OpenAI Speech API.

    Configuration:
        OPENAI_API_KEY
        OPENAI_TTS_MODEL   optional
        OPENAI_TTS_VOICE   optional
        OPENAI_TTS_SPEED   optional
    """

    API_URL = "https://api.openai.com/v1/audio/speech"
    MAX_INPUT_CHARS = 4096

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        timeout: int = 120,
    ) -> None:
        self.api_key = (
            os.getenv("OPENAI_API_KEY")
            if api_key is None
            else api_key
        ) or ""

        self.api_key = self.api_key.strip()
