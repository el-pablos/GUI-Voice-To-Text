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

HAS_FFMPEG = shutil.which("ffmpeg") is not None
skip_no_ffmpeg = pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg tidak tersedia di PATH")


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
        [".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".wma", ".mp4", ".mkv", ".mov", ".avi", ".webm"],
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
