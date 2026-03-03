"""Modul hashing — SHA256 buat cache key berdasarkan konten file."""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 8192


def hash_file(path: str | Path) -> str:
    """Hitung SHA256 hex digest dari file.

    Args:
        path: Path ke file audio/video.

    Returns:
        SHA256 hex string (64 karakter).
    """
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha.update(chunk)
    return sha.hexdigest()


def cache_key(file_hash: str, language: str = "id", model: str = "base", diarization: bool = False) -> str:
    """Buat cache key dari hash file + konfigurasi transkrip.

    Args:
        file_hash: SHA256 hash dari file.
        language: Kode bahasa.
        model: Model size (tiny/base/small/medium/large-v3).
        diarization: Apakah diarization aktif.

    Returns:
        String cache key unik.
    """
    parts = f"{file_hash}:{language}:{model}:diar={diarization}"
    return hashlib.sha256(parts.encode()).hexdigest()
