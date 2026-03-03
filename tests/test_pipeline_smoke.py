"""Smoke test pipeline — pakai mock engine biar cepat dan tanpa dependency berat."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.core.engines.base import BaseEngine, Segment, TranscriptResult
from app.core.pipeline import EXPORTERS, run_pipeline


class MockEngine(BaseEngine):
    """Engine palsu untuk testing pipeline tanpa transkrip asli."""

    @property
    def name(self) -> str:
        return "mock-engine"

    def is_available(self) -> bool:
        return True

    def transcribe(
        self,
        audio_path: str,
        language: str = "id",
        model_size: str = "base",
        **kwargs: Any,
    ) -> TranscriptResult:
        return TranscriptResult(
            segments=[
                Segment(start=0.0, end=1.5, text="Halo ini tes."),
                Segment(start=2.0, end=4.0, text="Pipeline berjalan lancar."),
                Segment(start=5.0, end=7.0, text="Selesai transkripsi."),
            ],
            language=language,
            duration=7.0,
            engine_name=self.name,
            model_name=model_size,
        )


@pytest.fixture()
def fake_audio(tmp_path: Path) -> Path:
    """Buat file audio palsu (WAV header minimal)."""
    f = tmp_path / "input.wav"
    # WAV header minimal biar is_supported lolos
    f.write_bytes(b"RIFF" + b"\x00" * 100)
    return f


class TestPipelineSmoke:
    @patch("app.core.pipeline.convert_to_wav")
    @patch("app.core.pipeline.probe_duration", return_value=7.0)
    def test_basic_pipeline(
        self,
        mock_probe: MagicMock,
        mock_convert: MagicMock,
        fake_audio: Path,
        tmp_path: Path,
    ) -> None:
        """Pipeline dasar harus export file tanpa error."""
        mock_convert.return_value = fake_audio  # skip convert

        output_dir = tmp_path / "output"
        result = run_pipeline(
            input_path=fake_audio,
            output_dir=output_dir,
            formats=["txt", "json"],
            use_cache=False,
            engine=MockEngine(),
        )

        assert result["segments_count"] == 3
        assert result["engine"] == "mock-engine"
        assert len(result["exported_files"]) == 2

        # Cek file benar terbuat
        for fpath in result["exported_files"]:
            assert Path(fpath).exists()

    @patch("app.core.pipeline.convert_to_wav")
    @patch("app.core.pipeline.probe_duration", return_value=7.0)
    def test_all_formats(
        self,
        mock_probe: MagicMock,
        mock_convert: MagicMock,
        fake_audio: Path,
        tmp_path: Path,
    ) -> None:
        """Pipeline harus bisa export semua format yang terdaftar."""
        mock_convert.return_value = fake_audio

        all_formats = list(EXPORTERS.keys())
        output_dir = tmp_path / "output"
        result = run_pipeline(
            input_path=fake_audio,
            output_dir=output_dir,
            formats=all_formats,
            use_cache=False,
            engine=MockEngine(),
        )

        assert len(result["exported_files"]) == len(all_formats)

    @patch("app.core.pipeline.convert_to_wav")
    @patch("app.core.pipeline.probe_duration", return_value=7.0)
    def test_progress_callback(
        self,
        mock_probe: MagicMock,
        mock_convert: MagicMock,
        fake_audio: Path,
        tmp_path: Path,
    ) -> None:
        """Progress callback harus dipanggil beberapa kali."""
        mock_convert.return_value = fake_audio

        stages: list[tuple[str, float]] = []

        def on_progress(stage: str, progress: float) -> None:
            stages.append((stage, progress))

        run_pipeline(
            input_path=fake_audio,
            output_dir=tmp_path / "output",
            use_cache=False,
            engine=MockEngine(),
            progress_callback=on_progress,
        )

        assert len(stages) >= 3
        assert stages[-1][1] == 1.0  # terakhir harus 100%

    @patch("app.core.pipeline.convert_to_wav")
    @patch("app.core.pipeline.probe_duration", return_value=7.0)
    def test_heuristic_diarization(
        self,
        mock_probe: MagicMock,
        mock_convert: MagicMock,
        fake_audio: Path,
        tmp_path: Path,
    ) -> None:
        """Pipeline dengan heuristic diarization harus assign speaker label."""
        mock_convert.return_value = fake_audio

        result = run_pipeline(
            input_path=fake_audio,
            output_dir=tmp_path / "output",
            formats=["json"],
            diarization_mode="heuristic",
            use_cache=False,
            engine=MockEngine(),
        )

        assert result["segments_count"] == 3

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        """File format tidak didukung harus raise ValueError."""
        f = tmp_path / "file.xyz"
        f.write_bytes(b"dummy")
        with pytest.raises(ValueError, match="tidak didukung"):
            run_pipeline(f, engine=MockEngine())

    def test_file_not_found_raises(self) -> None:
        """File tidak ada harus raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            run_pipeline("nonexistent.wav", engine=MockEngine())

    @patch("app.core.pipeline.convert_to_wav")
    @patch("app.core.pipeline.probe_duration", return_value=7.0)
    def test_filler_removal(
        self,
        mock_probe: MagicMock,
        mock_convert: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Pipeline dengan remove_filler harus bersihkan filler."""
        fake = tmp_path / "input.wav"
        fake.write_bytes(b"RIFF" + b"\x00" * 100)
        mock_convert.return_value = fake

        # Engine yang return teks dengan filler
        class FillerEngine(MockEngine):
            def transcribe(self, audio_path: str, **kwargs: Any) -> TranscriptResult:
                return TranscriptResult(
                    segments=[Segment(start=0.0, end=2.0, text="eee anu jadi begini.")],
                    language="id",
                    duration=2.0,
                    engine_name="mock",
                    model_name="base",
                )

        result = run_pipeline(
            fake,
            output_dir=tmp_path / "output",
            formats=["txt"],
            remove_filler=True,
            use_cache=False,
            engine=FillerEngine(),
        )
        assert result["segments_count"] == 1
