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
import re
import shutil
import wave
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

    The renderer creates WAV audio with Piper and converts it to MP3
    using FFmpeg.

    Standalone spoken-number markers such as ONE. / TWO. / THREE.
    receive dedicated emphasis: a longer pause before the marker and
    increased Piper volume for the marker itself.
    """

    DEFAULT_MODEL = Path(
        "tools/piper/voices/en_US-ryan-medium.onnx"
    )

    _NUMBER_WORD_RE = re.compile(
        r"^(?:"
        r"ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|"
        r"ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|"
        r"SEVENTEEN|EIGHTEEN|NINETEEN|TWENTY|THIRTY|FORTY|"
        r"FIFTY|SIXTY|SEVENTY|EIGHTY|NINETY|"
        r"(?:TWENTY|THIRTY|FORTY|FIFTY|SIXTY|SEVENTY|EIGHTY|NINETY)-"
        r"(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE)"
        r")$"
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

        # Number emphasis is intentionally local to standalone
        # production markers. The normal voice is unchanged.
        self.number_volume = 1.35
        self.number_pause_before = 0.60
        self.number_pause_after = 0.35

    @classmethod
    def _is_number_marker(
        cls,
        line: str,
    ) -> bool:
        value = str(line or "").strip()

        if not value.endswith("."):
            return False

        word = value[:-1].strip()

        return bool(
            cls._NUMBER_WORD_RE.fullmatch(word)
        )

    @classmethod
    def _split_number_markers(
        cls,
        script: str,
    ) -> list[tuple[str, str]]:
        """
        Split the script into normal text blocks and standalone
        spoken-number markers.

        The public script format is not changed.
        """
        parts: list[tuple[str, str]] = []
        current: list[str] = []

        for raw_line in script.splitlines():
            if cls._is_number_marker(raw_line):
                body = "\n".join(current).strip()

                if body:
                    parts.append(
                        ("body", body)
                    )

                number = (
                    raw_line.strip()[:-1].strip()
                )

                parts.append(
                    ("number", number)
                )

                current = []
            else:
                current.append(raw_line)

        body = "\n".join(current).strip()

        if body:
            parts.append(
                ("body", body)
            )

        return parts

    @staticmethod
    def _wav_silence(
        *,
        rate: int,
        channels: int,
        sample_width: int,
        seconds: float,
    ) -> bytes:
        frames = int(
            round(
                rate
                * max(0.0, float(seconds))
            )
        )

        return b"\x00" * (
            frames
            * channels
            * sample_width
        )

    def _render_piper_segment(
        self,
        text: str,
        wav_path: Path,
        *,
        volume: float | None = None,
        sentence_silence: float | None = None,
    ) -> None:
        command = [
            self.piper_binary,
            "--model",
            str(self.model_path),
            "--output_file",
            str(wav_path),
            "--sentence-silence",
            str(
                self.sentence_silence
                if sentence_silence is None
                else sentence_silence
            ),
        ]

        if volume is not None:
            command.extend(
                [
                    "--volume",
                    str(volume),
                ]
            )

        piper_result = subprocess.run(
            command,
            input=text,
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

        if (
            not wav_path.is_file()
            or wav_path.stat().st_size == 0
        ):
            raise RuntimeError(
                "Piper did not create an audio file"
            )

    @classmethod
    def _combine_wavs(
        cls,
        segments: list[tuple[str, Path]],
        output: Path,
        *,
        pause_before: float,
        pause_after: float,
    ) -> None:
        if not segments:
            raise RuntimeError(
                "No audio segments were generated"
            )

        reference = None

        for _, path in segments:
            with wave.open(
                str(path),
                "rb",
            ) as reader:
                current = (
                    reader.getnchannels(),
                    reader.getsampwidth(),
                    reader.getframerate(),
                    reader.getcomptype(),
                )

                if reference is None:
                    reference = current
                elif current != reference:
                    raise RuntimeError(
                        "Piper WAV segments have incompatible formats"
                    )

        assert reference is not None

        channels, sample_width, rate, comptype = (
            reference
        )

        if comptype != "NONE":
            raise RuntimeError(
                "Piper WAV must use uncompressed PCM audio"
            )

        with wave.open(
            str(output),
            "wb",
        ) as writer:
            writer.setnchannels(
                channels
            )
            writer.setsampwidth(
                sample_width
            )
            writer.setframerate(
                rate
            )
            writer.setcomptype(
                "NONE",
                "not compressed",
            )

            for kind, path in segments:
                if kind == "number":
                    writer.writeframes(
                        cls._wav_silence(
                            rate=rate,
                            channels=channels,
                            sample_width=sample_width,
                            seconds=pause_before,
                        )
                    )

                with wave.open(
                    str(path),
                    "rb",
                ) as reader:
                    writer.writeframes(
                        reader.readframes(
                            reader.getnframes()
                        )
                    )

                if kind == "number":
                    writer.writeframes(
                        cls._wav_silence(
                            rate=rate,
                            channels=channels,
                            sample_width=sample_width,
                            seconds=pause_after,
                        )
                    )

    def render(
        self,
        script: str,
        output_path: str | Path,
    ) -> Path:
        if not isinstance(
            script,
            str,
        ) or not script.strip():
            raise ValueError(
                "script must not be empty"
            )

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

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        parts = self._split_number_markers(
            script
        )

        has_number_markers = any(
            kind == "number"
            for kind, _ in parts
        )

        with tempfile.TemporaryDirectory(
            prefix="around-the-main-audio-"
        ) as temp_dir:
            temp_root = Path(temp_dir)

            if not has_number_markers:
                wav_path = (
                    temp_root / "voice.wav"
                )

                # This is the original rendering path.
                self._render_piper_segment(
                    script,
                    wav_path,
                )

            else:
                segments: list[
                    tuple[str, Path]
                ] = []

                for index, (
                    kind,
                    text,
                ) in enumerate(parts):
                    segment_path = (
                        temp_root
                        / f"segment-{index:03d}.wav"
                    )

                    if kind == "number":
                        self._render_piper_segment(
                            text,
                            segment_path,
                            volume=self.number_volume,
                            sentence_silence=0.0,
                        )
                    else:
                        self._render_piper_segment(
                            text,
                            segment_path,
                            volume=None,
                            sentence_silence=self.sentence_silence,
                        )

                    segments.append(
                        (
                            kind,
                            segment_path,
                        )
                    )

                wav_path = (
                    temp_root
                    / "voice-combined.wav"
                )

                self._combine_wavs(
                    segments,
                    wav_path,
                    pause_before=(
                        self.number_pause_before
                    ),
                    pause_after=(
                        self.number_pause_after
                    ),
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

        if (
            not output.is_file()
            or output.stat().st_size == 0
        ):
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
