"""Engine vosk — fallback offline ringan untuk device lemah."""

from __future__ import annotations

import json
import logging
import wave
from typing import Any

from app.core.engines.base import BaseEngine, Segment, TranscriptResult

logger = logging.getLogger(__name__)


class VoskEngine(BaseEngine):
    """STT engine menggunakan Vosk (lightweight offline)."""

    @property
    def name(self) -> str:
        return "vosk"

    def is_available(self) -> bool:
        try:
            import vosk  # noqa: F401

            return True
        except ImportError:
            return False

    def transcribe(
        self,
        audio_path: str,
        language: str = "id",
        model_size: str = "base",
        **kwargs: Any,
    ) -> TranscriptResult:
        """Transkrip menggunakan Vosk.

        Catatan: Vosk butuh model yang di-download terpisah.
        """
        try:
            import vosk
        except ImportError as e:
            raise ImportError("vosk belum terinstall. Jalankan: pip install vosk") from e

        model_path = kwargs.get("model_path", f"models/vosk-model-{language}")
        logger.info("Loading Vosk model dari '%s'...", model_path)

        model = vosk.Model(model_path)
        rec = vosk.KaldiRecognizer(model, 16000)

        wf = wave.open(audio_path, "rb")
        duration = wf.getnframes() / wf.getframerate()

        segments: list[Segment] = []
        current_time = 0.0

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text:
                    seg_duration = len(data) / (16000 * 2)  # approx
                    segments.append(
                        Segment(
                            start=current_time,
                            end=current_time + seg_duration,
                            text=text,
                        )
                    )
                    current_time += seg_duration

        # Final result
        final = json.loads(rec.FinalResult())
        if final.get("text"):
            segments.append(
                Segment(
                    start=current_time,
                    end=duration,
                    text=final["text"],
                )
            )

        wf.close()

        return TranscriptResult(
            segments=segments,
            language=language,
            duration=duration,
            engine_name=self.name,
            model_name=model_path,
        )
