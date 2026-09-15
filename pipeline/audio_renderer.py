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

from piper import PiperVoice
from piper.config import SynthesisConfig
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

        # Piper model is loaded once per renderer instance.
        # This avoids starting a new ONNX Runtime process for every
        # body/number segment during a full edition render.
        self._piper_voice = None

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

    @staticmethod
    def _spoken_number_marker(segment: str) -> str:
        """
        Convert an internal story-number marker into a clearer
        spoken phrase without changing the public audio script.

        Example:
            THREE -> Story three.
        """
        word = str(segment or "").strip().rstrip(".").strip()

        if not word:
            return segment

        return f"Story {word.lower()}."


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

    def _get_piper_voice(self) -> PiperVoice:
        if self._piper_voice is None:
            try:
                self._piper_voice = PiperVoice.load(
                    self.model_path
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to load Piper model: {exc}"
                ) from exc

        return self._piper_voice

    @staticmethod
    def _split_long_text(
        text: str,
        *,
        max_words: int = 24,
    ) -> list[str]:
        """
        Break unusually long spoken text at natural speech boundaries.

        Preference is given to punctuation boundaries. A hard word-count
        boundary is used only when a phrase remains too long.

        The source text is preserved word-for-word apart from whitespace
        normalization required to form the TTS phrases.
        """
        normalized = str(text or "").strip()

        if not normalized:
            return []

        paragraphs = [
            paragraph.strip()
            for paragraph in normalized.split("\n\n")
            if paragraph.strip()
        ]

        result: list[str] = []

        for paragraph in paragraphs:
            words = paragraph.split()

            if len(words) <= max_words:
                result.append(paragraph)
                continue

            current: list[str] = []

            for word in words:
                current.append(word)

                if len(current) < max_words:
                    continue

                phrase = " ".join(current).strip()

                # Prefer the last natural punctuation boundary inside
                # the candidate phrase.
                boundary = -1

                for punctuation in (";", ",", "-", ":"):
                    position = phrase.rfind(punctuation)
                    if position > boundary:
                        boundary = position

                # Only split at a punctuation boundary if enough words
                # remain before it. This prevents tiny fragments.
                if boundary > 0:
                    left = phrase[: boundary + 1].strip()
                    right = phrase[boundary + 1 :].strip()

                    left_words = left.split()

                    if (
                        len(left_words) >= 8
                        and right
                    ):
                        result.append(left)
                        current = right.split()
                        continue

                # No usable punctuation boundary: hard split.
                result.append(phrase)
                current = []

            if current:
                result.append(
                    " ".join(current).strip()
                )

        return result

    def _render_piper_segment(
        self,
        text: str,
        wav_path: Path,
        *,
        volume: float | None = None,
    ) -> None:
        voice = self._get_piper_voice()

        syn_config = SynthesisConfig(
            volume=(
                1.0
                if volume is None
                else float(volume)
            )
        )

        try:
            phrases = self._split_long_text(text)

            if not phrases:
                raise RuntimeError(
                    "Piper received empty text"
                )

            all_chunks = []

            for phrase in phrases:
                phrase_chunks = list(
                    voice.synthesize(
                        phrase,
                        syn_config,
                    )
                )

                if not phrase_chunks:
                    raise RuntimeError(
                        "Piper produced no audio chunks"
                    )

                all_chunks.extend(
                    phrase_chunks
                )

            first = all_chunks[0]

            with wave.open(
                str(wav_path),
                "wb",
            ) as writer:
                writer.setnchannels(
                    first.sample_channels
                )
                writer.setsampwidth(
                    first.sample_width
                )
                writer.setframerate(
                    first.sample_rate
                )
                writer.setcomptype(
                    "NONE",
                    "not compressed",
                )

                silence_frames = int(
                    round(
                        first.sample_rate
                        * max(
                            0.0,
                            self.sentence_silence,
                        )
                    )
                )

                silence = b"\x00" * (
                    silence_frames
                    * first.sample_channels
                    * first.sample_width
                )

                for index, chunk in enumerate(
                    all_chunks
                ):
                    if index > 0:
                        writer.writeframes(
                            silence
                        )

                    writer.writeframes(
                        chunk.audio_int16_bytes
                    )

        except Exception as exc:
            if isinstance(exc, RuntimeError):
                raise

            raise RuntimeError(
                f"Piper synthesis failed: {exc}"
            ) from exc

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
                            self._spoken_number_marker(text),
                            segment_path,
                            volume=self.number_volume,
                        )
                    else:
                        self._render_piper_segment(
                            text,
                            segment_path,
                            volume=None,
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
