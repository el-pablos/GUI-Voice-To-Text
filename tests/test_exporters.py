"""Test semua exporter — pastikan file terbuat dan isi valid."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.engines.base import Segment, TranscriptResult
from app.core.exporters.json_export import export_json
from app.core.exporters.md import export_md
from app.core.exporters.srt import export_srt
from app.core.exporters.txt import export_txt
from app.core.exporters.vtt import export_vtt


@pytest.fixture()
def sample_result() -> TranscriptResult:
    """Buat TranscriptResult contoh untuk testing."""
    return TranscriptResult(
        segments=[
            Segment(start=0.0, end=2.5, text="Halo selamat pagi.", speaker="Speaker 1"),
            Segment(start=3.0, end=5.5, text="Selamat pagi juga.", speaker="Speaker 2"),
            Segment(start=6.0, end=10.0, text="Kita mulai sidang hari ini.", speaker="Speaker 1"),
        ],
        language="id",
        duration=10.0,
        engine_name="faster-whisper",
        model_name="base",
        metadata={"beam_size": 5},
    )


@pytest.fixture()
def sample_no_speaker() -> TranscriptResult:
    """TranscriptResult tanpa speaker label."""
    return TranscriptResult(
        segments=[
            Segment(start=0.0, end=2.5, text="Halo dunia."),
            Segment(start=3.0, end=5.0, text="Tes tanpa speaker."),
        ],
        language="id",
        duration=5.0,
        engine_name="test",
        model_name="tiny",
    )


class TestTxtExporter:
    def test_creates_file(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_txt(sample_result, tmp_path / "out.txt")
        assert out.exists()
        assert out.suffix == ".txt"

    def test_contains_timestamp(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_txt(sample_result, tmp_path / "out.txt")
        content = out.read_text(encoding="utf-8")
        assert "[00:00]" in content
        assert "Halo selamat pagi." in content

    def test_contains_speaker(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_txt(sample_result, tmp_path / "out.txt")
        content = out.read_text(encoding="utf-8")
        assert "[Speaker 1]" in content

    def test_no_speaker(self, tmp_path: Path, sample_no_speaker: TranscriptResult) -> None:
        out = export_txt(sample_no_speaker, tmp_path / "out.txt")
        content = out.read_text(encoding="utf-8")
        assert "[Speaker" not in content


class TestMdExporter:
    def test_creates_file(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_md(sample_result, tmp_path / "out.md")
        assert out.exists()
        assert out.suffix == ".md"

    def test_has_heading(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_md(sample_result, tmp_path / "out.md")
        content = out.read_text(encoding="utf-8")
        assert "# Transkrip Wawancara" in content

    def test_has_metadata(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_md(sample_result, tmp_path / "out.md")
        content = out.read_text(encoding="utf-8")
        assert "**Bahasa**" in content
        assert "**Durasi**" in content


class TestSrtExporter:
    def test_creates_file(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_srt(sample_result, tmp_path / "out.srt")
        assert out.exists()
        assert out.suffix == ".srt"

    def test_srt_format(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_srt(sample_result, tmp_path / "out.srt")
        content = out.read_text(encoding="utf-8")
        assert "-->" in content
        assert "00:00:00,000" in content

    def test_has_sequence_numbers(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_srt(sample_result, tmp_path / "out.srt")
        lines = out.read_text(encoding="utf-8").strip().split("\n")
        assert lines[0] == "1"


class TestVttExporter:
    def test_creates_file(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_vtt(sample_result, tmp_path / "out.vtt")
        assert out.exists()
        assert out.suffix == ".vtt"

    def test_webvtt_header(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_vtt(sample_result, tmp_path / "out.vtt")
        content = out.read_text(encoding="utf-8")
        assert content.startswith("WEBVTT")

    def test_vtt_time_format(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_vtt(sample_result, tmp_path / "out.vtt")
        content = out.read_text(encoding="utf-8")
        assert "." in content  # VTT pakai titik, bukan koma


class TestJsonExporter:
    def test_creates_file(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_json(sample_result, tmp_path / "out.json")
        assert out.exists()
        assert out.suffix == ".json"

    def test_valid_json(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        out = export_json(sample_result, tmp_path / "out.json")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "segments" in data
        assert len(data["segments"]) == 3

    def test_roundtrip(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        """Export ke JSON lalu baca balik harus konsisten."""
        out = export_json(sample_result, tmp_path / "out.json")
        data = json.loads(out.read_text(encoding="utf-8"))
        restored = TranscriptResult.from_dict(data)
        assert len(restored.segments) == len(sample_result.segments)
        assert restored.language == sample_result.language


class TestDocxExporter:
    def test_creates_file(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        from app.core.exporters.docx_export import export_docx

        out = export_docx(sample_result, tmp_path / "out.docx")
        assert out.exists()
        assert out.suffix == ".docx"
        assert out.stat().st_size > 0

    def test_docx_has_content(self, tmp_path: Path, sample_result: TranscriptResult) -> None:
        from docx import Document

        from app.core.exporters.docx_export import export_docx

        out = export_docx(sample_result, tmp_path / "out.docx")
        doc = Document(str(out))
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "Transkrip Wawancara" in full_text
        assert "Halo selamat pagi." in full_text


class TestEmptyResult:
    """Test semua exporter dengan result kosong — harus tetap berhasil."""

    @pytest.fixture()
    def empty_result(self) -> TranscriptResult:
        return TranscriptResult()

    def test_txt_empty(self, tmp_path: Path, empty_result: TranscriptResult) -> None:
        out = export_txt(empty_result, tmp_path / "empty.txt")
        assert out.exists()

    def test_md_empty(self, tmp_path: Path, empty_result: TranscriptResult) -> None:
        out = export_md(empty_result, tmp_path / "empty.md")
        assert out.exists()

    def test_srt_empty(self, tmp_path: Path, empty_result: TranscriptResult) -> None:
        out = export_srt(empty_result, tmp_path / "empty.srt")
        assert out.exists()

    def test_vtt_empty(self, tmp_path: Path, empty_result: TranscriptResult) -> None:
        out = export_vtt(empty_result, tmp_path / "empty.vtt")
        assert out.exists()

    def test_json_empty(self, tmp_path: Path, empty_result: TranscriptResult) -> None:
        out = export_json(empty_result, tmp_path / "empty.json")
        assert out.exists()
