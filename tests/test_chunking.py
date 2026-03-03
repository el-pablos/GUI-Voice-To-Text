"""Unit tests for app.core.chunking module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.chunking import (
    CHUNK_THRESHOLD_SECONDS,
    CHUNK_THRESHOLD_SIZE_MB,
    DEFAULT_CHUNK_SECONDS,
    cleanup_chunks,
    iterate_audio_chunks,
    should_chunk,
)


class TestShouldChunk:
    """Tests for should_chunk()."""

    def test_short_file_no_chunk(self) -> None:
        assert should_chunk(300) is False

    def test_exact_threshold_no_chunk(self) -> None:
        assert should_chunk(CHUNK_THRESHOLD_SECONDS) is False

    def test_above_threshold_chunk(self) -> None:
        assert should_chunk(CHUNK_THRESHOLD_SECONDS + 1) is True

    def test_small_size_no_chunk(self) -> None:
        small = 50 * 1024 * 1024  # 50 MB
        assert should_chunk(300, file_size_bytes=small) is False

    def test_large_size_chunk(self) -> None:
        big = (CHUNK_THRESHOLD_SIZE_MB + 1) * 1024 * 1024
        assert should_chunk(300, file_size_bytes=big) is True

    def test_exactly_at_size_threshold_no_chunk(self) -> None:
        exact = CHUNK_THRESHOLD_SIZE_MB * 1024 * 1024
        assert should_chunk(300, file_size_bytes=exact) is False

    def test_long_duration_overrides_small_size(self) -> None:
        assert should_chunk(5000, file_size_bytes=1024) is True


class TestIterateAudioChunks:
    """Tests for iterate_audio_chunks()."""

    @patch("app.core.chunking.find_ffmpeg", return_value=None)
    def test_no_ffmpeg_raises(self, _mock: MagicMock) -> None:
        with pytest.raises(FileNotFoundError, match="ffmpeg"):
            iterate_audio_chunks("dummy.wav", total_duration=120)

    @patch("app.core.chunking.subprocess.run")
    @patch("app.core.chunking.find_ffmpeg", return_value="ffmpeg")
    def test_single_chunk(
        self,
        _mock_ff: MagicMock,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """File shorter than chunk_seconds produces 1 chunk."""
        src = tmp_path / "test.wav"
        src.write_bytes(b"\x00" * 100)

        mock_run.return_value = MagicMock(returncode=0, stderr="")

        # We need the chunk file to exist after subprocess.run
        def side_effect(cmd, **kwargs):
            # cmd[-1] is the output path
            out = Path(cmd[-1])
            out.write_bytes(b"\x00" * 10)
            return MagicMock(returncode=0, stderr="")

        mock_run.side_effect = side_effect

        chunks = iterate_audio_chunks(
            src, chunk_seconds=DEFAULT_CHUNK_SECONDS, total_duration=500
        )
        assert len(chunks) == 1
        assert chunks[0].name == "chunk_0000.wav"

        # Cleanup
        cleanup_chunks(chunks)

    @patch("app.core.chunking.subprocess.run")
    @patch("app.core.chunking.find_ffmpeg", return_value="ffmpeg")
    def test_multiple_chunks(
        self,
        _mock_ff: MagicMock,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """File 2500 seconds with 600s chunk → ceil(2500/600) = 5 chunks."""
        src = tmp_path / "long.wav"
        src.write_bytes(b"\x00" * 100)

        def side_effect(cmd, **kwargs):
            out = Path(cmd[-1])
            out.write_bytes(b"\x00" * 10)
            return MagicMock(returncode=0, stderr="")

        mock_run.side_effect = side_effect

        chunks = iterate_audio_chunks(
            src, chunk_seconds=600, total_duration=2500
        )
        # 0-599, 600-1199, 1200-1799, 1800-2399, 2400-2500 → 5 chunks
        assert len(chunks) == 5
        assert mock_run.call_count == 5

        cleanup_chunks(chunks)

    @patch("app.core.chunking.subprocess.run")
    @patch("app.core.chunking.find_ffmpeg", return_value="ffmpeg")
    def test_chunk_extraction_failure_stops(
        self,
        _mock_ff: MagicMock,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """If ffmpeg returns error and file not created, stop chunking."""
        src = tmp_path / "bad.wav"
        src.write_bytes(b"\x00" * 100)

        # First chunk OK, second fails (file not created)
        call_count = 0

        def side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            out = Path(cmd[-1])
            if call_count == 1:
                out.write_bytes(b"\x00" * 10)
                return MagicMock(returncode=0, stderr="")
            else:
                return MagicMock(returncode=1, stderr="error")

        mock_run.side_effect = side_effect

        chunks = iterate_audio_chunks(
            src, chunk_seconds=600, total_duration=1800
        )
        assert len(chunks) == 1

        cleanup_chunks(chunks)


class TestCleanupChunks:
    """Tests for cleanup_chunks()."""

    def test_cleanup_removes_files(self, tmp_path: Path) -> None:
        chunk_dir = tmp_path / "chunks"
        chunk_dir.mkdir()
        files = []
        for i in range(3):
            f = chunk_dir / f"chunk_{i:04d}.wav"
            f.write_bytes(b"\x00" * 10)
            files.append(f)

        cleanup_chunks(files)

        for f in files:
            assert not f.exists()
        # Dir should be removed too (empty after cleanup)
        assert not chunk_dir.exists()

    def test_cleanup_empty_list(self) -> None:
        """No error when cleaning up an empty list."""
        cleanup_chunks([])

    def test_cleanup_missing_files(self, tmp_path: Path) -> None:
        """No error when files are already gone."""
        missing = [tmp_path / "nope.wav"]
        cleanup_chunks(missing)  # Should not raise
