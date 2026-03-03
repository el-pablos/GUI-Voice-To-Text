"""Test modul hashing — deterministik dan cache key unik."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.core.hashing import cache_key, hash_file


class TestHashFile:
    def test_deterministic(self, tmp_path: Path) -> None:
        """Hash file yang sama harus menghasilkan digest yang sama."""
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world" * 100)
        assert hash_file(f) == hash_file(f)

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        """File beda konten harus beda hash."""
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "b.bin"
        f1.write_bytes(b"aaa")
        f2.write_bytes(b"bbb")
        assert hash_file(f1) != hash_file(f2)

    def test_known_digest(self, tmp_path: Path) -> None:
        """Hash harus cocok dengan hashlib standar."""
        import hashlib

        data = b"test data for hashing"
        f = tmp_path / "known.bin"
        f.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert hash_file(f) == expected

    def test_empty_file(self, tmp_path: Path) -> None:
        """File kosong harus tetap menghasilkan hash valid."""
        import hashlib

        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert hash_file(f) == expected


class TestCacheKey:
    def test_same_config_same_key(self) -> None:
        """Config yang sama harus menghasilkan cache key yang sama."""
        h = "abc123"
        assert cache_key(h, "id", "base", False) == cache_key(h, "id", "base", False)

    def test_different_language(self) -> None:
        """Bahasa beda → cache key beda."""
        h = "abc123"
        assert cache_key(h, "id") != cache_key(h, "en")

    def test_different_model(self) -> None:
        """Model beda → cache key beda."""
        h = "abc123"
        assert cache_key(h, "id", "base") != cache_key(h, "id", "small")

    def test_different_diarization(self) -> None:
        """Diarization on/off → cache key beda."""
        h = "abc123"
        assert cache_key(h, diarization=False) != cache_key(h, diarization=True)

    def test_different_file_hash(self) -> None:
        """File hash beda → cache key beda."""
        assert cache_key("aaa") != cache_key("bbb")
