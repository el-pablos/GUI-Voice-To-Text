"""Base interface untuk STT engine — semua engine harus implement ini."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Segment:
    """Satu segmen hasil transkrip."""

    start: float  # detik
    end: float  # detik
    text: str
    speaker: str = ""  # kosong = belum ada diarization
    confidence: float = 0.0


@dataclass
class TranscriptResult:
    """Hasil lengkap transkrip dari engine."""

    segments: list[Segment] = field(default_factory=list)
    language: str = ""
    duration: float = 0.0
    engine_name: str = ""
    model_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        """Gabung semua segmen jadi teks penuh."""
        return " ".join(seg.text.strip() for seg in self.segments if seg.text.strip())

    def to_dict(self) -> dict[str, Any]:
        """Convert ke dict untuk serialisasi/cache."""
        return {
            "segments": [
                {
                    "start": s.start,
                    "end": s.end,
                    "text": s.text,
                    "speaker": s.speaker,
                    "confidence": s.confidence,
                }
                for s in self.segments
            ],
            "language": self.language,
            "duration": self.duration,
            "engine_name": self.engine_name,
            "model_name": self.model_name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TranscriptResult:
        """Buat TranscriptResult dari dict (misalnya dari cache)."""
        segments = [Segment(**s) for s in data.get("segments", [])]
        return cls(
            segments=segments,
            language=data.get("language", ""),
            duration=data.get("duration", 0.0),
            engine_name=data.get("engine_name", ""),
            model_name=data.get("model_name", ""),
            metadata=data.get("metadata", {}),
        )


class BaseEngine(ABC):
    """Abstract base class untuk semua STT engine."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nama engine."""
        ...

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: str = "id",
        model_size: str = "base",
        **kwargs: Any,
    ) -> TranscriptResult:
        """Jalankan transkrip.

        Args:
            audio_path: Path ke file WAV (sudah di-convert).
            language: Kode bahasa.
            model_size: Ukuran model.
            **kwargs: Parameter tambahan engine-specific.

        Returns:
            TranscriptResult dengan segmen-segmen transkrip.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Cek apakah engine ini bisa dipakai (dependency tersedia)."""
        ...


def get_available_engines() -> list[type[BaseEngine]]:
    """Daftar engine yang tersedia (dependency terpasang)."""
    engines: list[type[BaseEngine]] = []

    try:
        from app.core.engines.faster_whisper import FasterWhisperEngine

        if FasterWhisperEngine().is_available():
            engines.append(FasterWhisperEngine)
    except ImportError:
        pass

    try:
        from app.core.engines.vosk_engine import VoskEngine

        if VoskEngine().is_available():
            engines.append(VoskEngine)
    except ImportError:
        pass

    return engines
