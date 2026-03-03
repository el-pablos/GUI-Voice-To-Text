"""Engine faster-whisper — default offline STT via CTranslate2."""

from __future__ import annotations

import logging
from typing import Any

from app.core.engines.base import BaseEngine, Segment, TranscriptResult

logger = logging.getLogger(__name__)


class FasterWhisperEngine(BaseEngine):
    """STT engine menggunakan faster-whisper (Whisper via CTranslate2)."""

    @property
    def name(self) -> str:
        return "faster-whisper"

    def is_available(self) -> bool:
        """Cek apakah faster-whisper terinstall."""
        try:
            import faster_whisper  # noqa: F401

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
        """Jalankan transkrip menggunakan faster-whisper.

        Args:
            audio_path: Path ke file WAV.
            language: Kode bahasa (misal 'id', 'en').
            model_size: Model size (tiny/base/small/medium/large-v3).
            **kwargs: beam_size, vad_filter, dll.

        Returns:
            TranscriptResult.
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise ImportError("faster-whisper belum terinstall. Jalankan: pip install faster-whisper") from e

        logger.info("Loading model faster-whisper '%s'...", model_size)
        device = kwargs.get("device", "cpu")
        compute_type = kwargs.get("compute_type", "int8")

        model = WhisperModel(model_size, device=device, compute_type=compute_type)

        logger.info("Mulai transkrip '%s' (bahasa=%s)...", audio_path, language)
        beam_size = kwargs.get("beam_size", 5)
        vad_filter = kwargs.get("vad_filter", True)

        segments_gen, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=beam_size,
            vad_filter=vad_filter,
        )

        segments: list[Segment] = []
        for seg in segments_gen:
            segments.append(
                Segment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text.strip(),
                    confidence=seg.avg_log_prob if hasattr(seg, "avg_log_prob") else 0.0,
                )
            )

        logger.info("Transkrip selesai: %d segmen, durasi %.1fs", len(segments), info.duration)

        return TranscriptResult(
            segments=segments,
            language=info.language,
            duration=info.duration,
            engine_name=self.name,
            model_name=model_size,
            metadata={
                "language_probability": info.language_probability,
                "beam_size": beam_size,
                "vad_filter": vad_filter,
            },
        )
