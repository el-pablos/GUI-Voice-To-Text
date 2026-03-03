"""Test FFmpeg wrapper — detect, probe, convert.

Catatan: Test yang butuh ffmpeg binary di-skip otomatis jika ffmpeg tidak tersedia.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.ffmpeg import (
    convert_to_wav,
    find_ffmpeg,
    find_ffprobe,
    is_supported,
    probe_duration,
)

HAS_FFMPEG = find_ffmpeg() is not None
skip_no_ffmpeg = pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg tidak tersedia")

# Path ke fixture MPEG
FIXTURE_SIDANG = Path("tests/fixtures/sidang_masukan.mpeg")
FIXTURE_JERNIH = Path("tests/fixtures/versi_jernih.mpeg")
HAS_MPEG_FIXTURES = FIXTURE_SIDANG.exists() and FIXTURE_JERNIH.exists()
skip_no_mpeg = pytest.mark.skipif(
    not HAS_MPEG_FIXTURES, reason="fixture MPEG tidak ada (file besar, tidak di-commit)"
)


class TestFindFFmpeg:
    def test_returns_string_or_none(self) -> None:
        """find_ffmpeg harus return str atau None."""
        result = find_ffmpeg()
        assert result is None or isinstance(result, str)

    def test_portable_path_detection(self, tmp_path: Path) -> None:
        """Jika ada file portable di tools/ffmpeg/, harus diprioritaskan."""
        fake_ffmpeg = tmp_path / "tools" / "ffmpeg" / "ffmpeg.exe"
        fake_ffmpeg.parent.mkdir(parents=True)
        fake_ffmpeg.write_text("fake")

        fake_module = tmp_path / "app" / "core" / "ffmpeg.py"
        fake_module.parent.mkdir(parents=True)
        fake_module.write_text("")

        with patch("app.core.ffmpeg.__file__", str(fake_module)):
            result = find_ffmpeg()
            assert result is not None
            assert "ffmpeg.exe" in result


class TestFindFFprobe:
    def test_returns_string_or_none(self) -> None:
        result = find_ffprobe()
        assert result is None or isinstance(result, str)


class TestIsSupported:
    @pytest.mark.parametrize(
        "ext",
        [".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".wma", ".mpeg", ".mpga", ".mp4", ".mkv", ".mov", ".avi", ".webm"],
    )
    def test_supported_extensions(self, ext: str) -> None:
        assert is_supported(f"file{ext}")

    @pytest.mark.parametrize("ext", [".pdf", ".docx", ".py", ".exe", ".txt"])
    def test_unsupported_extensions(self, ext: str) -> None:
        assert not is_supported(f"file{ext}")


class TestProbe:
    @skip_no_ffmpeg
    def test_probe_real_file(self) -> None:
        """Probe file test fixture (perlu ffmpeg + fixture)."""
        fixture = Path("tests/fixtures/sample_sidang.mp3")
        if not fixture.exists():
            pytest.skip("fixture sample_sidang.mp3 tidak ada")
        dur = probe_duration(fixture)
        assert dur > 0

    def test_probe_no_ffprobe_raises(self, tmp_path: Path) -> None:
        """Harus raise FileNotFoundError jika ffprobe tidak ada."""
        f = tmp_path / "fake.mp3"
        f.write_bytes(b"\x00" * 100)
        with patch("app.core.ffmpeg.find_ffprobe", return_value=None):
            with pytest.raises(FileNotFoundError):
                probe_duration(f)


class TestConvert:
    @skip_no_ffmpeg
    def test_convert_real_file(self, tmp_path: Path) -> None:
        """Convert file test fixture ke WAV (perlu ffmpeg + fixture)."""
        fixture = Path("tests/fixtures/sample_sidang.mp3")
        if not fixture.exists():
            pytest.skip("fixture sample_sidang.mp3 tidak ada")
        out = convert_to_wav(fixture, tmp_path / "out.wav")
        assert out.exists()
        assert out.suffix == ".wav"
        assert out.stat().st_size > 0

    def test_convert_no_ffmpeg_raises(self, tmp_path: Path) -> None:
        """Harus raise FileNotFoundError jika ffmpeg tidak ada."""
        f = tmp_path / "fake.mp3"
        f.write_bytes(b"\x00" * 100)
        with patch("app.core.ffmpeg.find_ffmpeg", return_value=None):
            with pytest.raises(FileNotFoundError):
                convert_to_wav(f)


class TestMpegSupport:
    """Integration test untuk file MPEG asli.

    File fixture besar (~35-90 MB) tidak di-push ke GitHub.
    Test ini akan di-skip otomatis jika fixture tidak ada.
    """

    def test_mpeg_is_supported(self) -> None:
        """Format .mpeg harus dikenali sebagai supported."""
        assert is_supported("audio.mpeg")
        assert is_supported("audio.mpga")
        assert is_supported("rekaman.MPEG")

    @skip_no_ffmpeg
    @skip_no_mpeg
    def test_probe_mpeg_sidang(self) -> None:
        """Probe durasi sidang_masukan.mpeg (~38 menit)."""
        dur = probe_duration(FIXTURE_SIDANG)
        assert dur > 2000, f"Durasi terlalu pendek: {dur}s"
        assert dur < 3000, f"Durasi terlalu panjang: {dur}s"

    @skip_no_ffmpeg
    @skip_no_mpeg
    def test_probe_mpeg_jernih(self) -> None:
        """Probe durasi versi_jernih.mpeg (~38 menit)."""
        dur = probe_duration(FIXTURE_JERNIH)
        assert dur > 2000, f"Durasi terlalu pendek: {dur}s"
        assert dur < 3000, f"Durasi terlalu panjang: {dur}s"

    @skip_no_ffmpeg
    @skip_no_mpeg
    def test_convert_mpeg_to_wav(self, tmp_path: Path) -> None:
        """Convert versi_jernih.mpeg ke WAV, hasilnya harus valid."""
        out = convert_to_wav(FIXTURE_JERNIH, tmp_path / "jernih.wav")
        assert out.exists()
        assert out.suffix == ".wav"
        assert out.stat().st_size > 1_000_000, "WAV output terlalu kecil"

    @skip_no_ffmpeg
    @skip_no_mpeg
    def test_convert_mpeg_sidang_to_wav(self, tmp_path: Path) -> None:
        """Convert sidang_masukan.mpeg ke WAV, hasilnya harus valid."""
        out = convert_to_wav(FIXTURE_SIDANG, tmp_path / "sidang.wav")
        assert out.exists()
        assert out.suffix == ".wav"
        assert out.stat().st_size > 1_000_000, "WAV output terlalu kecil"
