"""Wrapper FFmpeg — detect, probe, dan convert audio/video."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

# Ekstensi yang didukung
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".wma", ".mpeg", ".mpga"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}
SUPPORTED_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS

# Default output format untuk STT
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1


def find_ffmpeg() -> str | None:
    """Cari ffmpeg executable.

    Urutan pencarian:
    1. Folder tools/ffmpeg/ (portable bundle)
    2. System PATH
    3. Environment variable FFMPEG_PATH

    Returns:
        Path ke ffmpeg executable, atau None jika tidak ditemukan.
    """
    # 1. Cek portable bundle
    portable = Path(__file__).resolve().parents[2] / "tools" / "ffmpeg" / "ffmpeg.exe"
    if portable.is_file():
        return str(portable)

    # 2. Cek system PATH
    found = shutil.which("ffmpeg")
    if found:
        return found

    # 3. Cek environment variable
    env_path = os.environ.get("FFMPEG_PATH")
    if env_path and Path(env_path).is_file():
        return env_path

    return None


def find_ffprobe() -> str | None:
    """Cari ffprobe executable (analog dengan find_ffmpeg)."""
    portable = Path(__file__).resolve().parents[2] / "tools" / "ffmpeg" / "ffprobe.exe"
    if portable.is_file():
        return str(portable)

    found = shutil.which("ffprobe")
    if found:
        return found

    env_path = os.environ.get("FFPROBE_PATH")
    if env_path and Path(env_path).is_file():
        return env_path

    return None


def probe_duration(input_path: str | Path) -> float:
    """Ambil durasi file audio/video dalam detik menggunakan ffprobe.

    Args:
        input_path: Path ke file media.

    Returns:
        Durasi dalam detik.

    Raises:
        FileNotFoundError: Jika ffprobe tidak ditemukan.
        RuntimeError: Jika ffprobe gagal.
    """
    ffprobe = find_ffprobe()
    if not ffprobe:
        raise FileNotFoundError("ffprobe tidak ditemukan. Install FFmpeg atau taruh di tools/ffmpeg/.")

    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(input_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe gagal: {result.stderr}")

    data: dict[str, Any] = json.loads(result.stdout)
    duration_str = data.get("format", {}).get("duration", "0")
    return float(duration_str)


def convert_to_wav(
    input_path: str | Path,
    output_path: str | Path | None = None,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    channels: int = DEFAULT_CHANNELS,
) -> Path:
    """Convert file audio/video ke WAV standar untuk STT engine.

    Args:
        input_path: Path ke file media input.
        output_path: Path output WAV. Jika None, auto-generate di folder yang sama.
        sample_rate: Sample rate output (default 16000).
        channels: Jumlah channel (default 1 = mono).

    Returns:
        Path ke file WAV hasil konversi.

    Raises:
        FileNotFoundError: Jika ffmpeg tidak ditemukan.
        RuntimeError: Jika konversi gagal.
    """
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise FileNotFoundError("ffmpeg tidak ditemukan. Install FFmpeg atau taruh di tools/ffmpeg/.")

    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_suffix(".wav")
    output_path = Path(output_path)

    # Pastikan folder output ada
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg,
        "-y",  # overwrite tanpa tanya
        "-i", str(input_path),
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-c:a", "pcm_s16le",
        str(output_path),
    ]

    # Timeout dinamis berdasarkan durasi file, biar file panjang ga keputus
    try:
        duration = probe_duration(input_path)
    except Exception:
        duration = 0.0

    if duration > 0:
        timeout_seconds = max(600, int(duration * 3) + 120)
    else:
        # Fallback besar (6 jam) kalau durasi ga bisa dideteksi
        timeout_seconds = 21600

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg convert gagal: {result.stderr[:500]}")

    return output_path


def is_supported(path: str | Path) -> bool:
    """Cek apakah ekstensi file didukung."""
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
