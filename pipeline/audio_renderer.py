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
        sentence_silence: float = 0.35,
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

        self.model = (
            model
            or os.getenv("OPENAI_TTS_MODEL")
            or "gpt-4o-mini-tts"
        ).strip()

        self.voice = (
            voice
            or os.getenv("OPENAI_TTS_VOICE")
            or "onyx"
        ).strip()

        raw_speed = (
            str(speed)
            if speed is not None
            else os.getenv("OPENAI_TTS_SPEED", "1.0")
        )

        try:
            self.speed = float(raw_speed)
        except (TypeError, ValueError):
            self.speed = 1.0

        self.timeout = int(timeout)

    def _request(self, text: str) -> bytes:
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured"
            )

        payload = {
            "model": self.model,
            "voice": self.voice,
            "input": text,
            "response_format": "mp3",
            "speed": self.speed,
        }

        request = urllib.request.Request(
            self.API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                data = response.read()

        except urllib.error.HTTPError as exc:
            body = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            raise RuntimeError(
                f"OpenAI TTS HTTP {exc.code}: {body}"
            ) from exc

        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"OpenAI TTS connection failed: {exc.reason}"
            ) from exc

        if not data:
            raise RuntimeError(
                "OpenAI TTS returned an empty audio response"
            )

        return data

    @staticmethod
    def _split_script(script: str) -> list[str]:
        script = script.strip()

        if len(script) <= OpenAITTSRenderer.MAX_INPUT_CHARS:
            return [script]

        paragraphs = [
            p.strip()
            for p in script.split("\n\n")
            if p.strip()
        ]

        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            candidate = (
                paragraph
                if not current
                else f"{current}\n\n{paragraph}"
            )

            if len(candidate) <= OpenAITTSRenderer.MAX_INPUT_CHARS:
                current = candidate
                continue

            if current:
                chunks.append(current)
                current = ""

            if len(paragraph) <= OpenAITTSRenderer.MAX_INPUT_CHARS:
                current = paragraph
                continue

            words = paragraph.split()
            word_chunk = ""

            for word in words:
                candidate = (
                    word
                    if not word_chunk
                    else f"{word_chunk} {word}"
                )

                if len(candidate) <= OpenAITTSRenderer.MAX_INPUT_CHARS:
                    word_chunk = candidate
                else:
                    if word_chunk:
                        chunks.append(word_chunk)
                    word_chunk = word

            if word_chunk:
                current = word_chunk

        if current:
            chunks.append(current)

        return chunks

    def render(
        self,
        script: str,
        output_path: str | Path,
    ) -> Path:
        if not isinstance(script, str) or not script.strip():
            raise ValueError("script must not be empty")

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        chunks = self._split_script(script)

        audio_parts: list[bytes] = []

        for chunk in chunks:
            audio_parts.append(
                self._request(chunk)
            )

        output.write_bytes(
            b"".join(audio_parts)
        )

        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(
                "Audio file was not created"
            )

        return output
