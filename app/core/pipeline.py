"""Pipeline orchestrator — convert → cache check → transcribe → postprocess → export."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any, Callable

from app.core.cache import get_cache, set_cache
from app.core.engines.base import BaseEngine, TranscriptResult
from app.core.exporters.json_export import export_json
from app.core.exporters.md import export_md
from app.core.exporters.srt import export_srt
from app.core.exporters.txt import export_txt
from app.core.exporters.vtt import export_vtt
from app.core.ffmpeg import convert_to_wav, is_supported, probe_duration
from app.core.hashing import cache_key, hash_file
from app.core.postprocess.cleanup import cleanup_text
from app.core.postprocess.segmentation import heuristic_diarization

logger = logging.getLogger(__name__)

# Mapping format ke exporter
EXPORTERS: dict[str, Callable[..., Path]] = {
    "txt": export_txt,
    "md": export_md,
    "srt": export_srt,
    "vtt": export_vtt,
    "json": export_json,
}

# DOCX opsional (butuh python-docx)
try:
    from app.core.exporters.docx_export import export_docx

    EXPORTERS["docx"] = export_docx
except ImportError:
    pass


def _get_default_engine() -> BaseEngine:
    """Ambil engine default (faster-whisper atau fallback)."""
    try:
        from app.core.engines.faster_whisper import FasterWhisperEngine

        engine = FasterWhisperEngine()
        if engine.is_available():
            return engine
    except ImportError:
        pass

    try:
        from app.core.engines.vosk_engine import VoskEngine

        engine = VoskEngine()
        if engine.is_available():
            return engine
    except ImportError:
        pass

    raise RuntimeError("Tidak ada STT engine yang tersedia. Install faster-whisper atau vosk.")


def run_pipeline(
    input_path: str | Path,
    output_dir: str | Path = "output",
    formats: list[str] | None = None,
    language: str = "id",
    model_size: str = "base",
    use_cache: bool = True,
    remove_filler: bool = False,
    diarization_mode: str = "none",
    engine: BaseEngine | None = None,
    progress_callback: Callable[[str, float], None] | None = None,
) -> dict[str, Any]:
    """Jalankan pipeline transkrip end-to-end.

    Args:
        input_path: Path ke file audio/video.
        output_dir: Folder output.
        formats: List format export (default: ["txt"]).
        language: Kode bahasa.
        model_size: Model size.
        use_cache: Gunakan Redis cache.
        remove_filler: Hapus filler words.
        diarization_mode: "none" / "heuristic" / "advanced".
        engine: STT engine instance. None = auto-detect.
        progress_callback: Callback (stage, progress_0_to_1).

    Returns:
        Dict berisi info hasil: exported_files, duration, cached, dll.
    """
    if formats is None:
        formats = ["txt"]

    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {input_path}")

    if not is_supported(input_path):
        raise ValueError(f"Format file tidak didukung: {input_path.suffix}")

    _notify(progress_callback, "Memulai...", 0.0)

    # Step 1: Hash file
    _notify(progress_callback, "Menghitung hash file...", 0.05)
    file_hash = hash_file(input_path)
    logger.info("File hash: %s", file_hash[:16])

    # Step 2: Cache check
    ck = cache_key(file_hash, language, model_size, diarization_mode != "none")
    cached_data = None
    if use_cache:
        _notify(progress_callback, "Mengecek cache...", 0.1)
        cached_data = get_cache(ck)

    result: TranscriptResult
    if cached_data:
        logger.info("Cache HIT — skip transkrip")
        result = TranscriptResult.from_dict(cached_data)
        _notify(progress_callback, "Cache hit!", 0.7)
    else:
        # Step 3: Convert ke WAV
        _notify(progress_callback, "Mengkonversi audio...", 0.15)
        if input_path.suffix.lower() == ".wav":
            wav_path = input_path
            temp_wav = None
        else:
            temp_dir = tempfile.mkdtemp(prefix="transkrip_")
            wav_path = Path(temp_dir) / "converted.wav"
            wav_path = convert_to_wav(input_path, wav_path)
            temp_wav = wav_path

        # Step 4: Probe durasi
        try:
            duration = probe_duration(wav_path)
        except Exception:
            duration = 0.0

        # Step 5: Transcribe
        _notify(progress_callback, "Mentranskrip audio...", 0.25)
        if engine is None:
            engine = _get_default_engine()

        result = engine.transcribe(
            audio_path=str(wav_path),
            language=language,
            model_size=model_size,
        )

        if duration > 0 and result.duration == 0:
            result.duration = duration

        # Step 6: Postprocess
        _notify(progress_callback, "Memproses teks...", 0.65)
        for seg in result.segments:
            seg.text = cleanup_text(seg.text, remove_filler=remove_filler)

        if diarization_mode == "heuristic":
            result = heuristic_diarization(result)

        # Step 7: Cache set
        if use_cache:
            set_cache(ck, result.to_dict())

        # Cleanup temp
        if temp_wav and temp_wav.exists():
            try:
                temp_wav.unlink()
                temp_wav.parent.rmdir()
            except Exception:
                pass

    # Step 8: Export
    _notify(progress_callback, "Mengekspor hasil...", 0.75)
    exported_files: list[str] = []
    stem = input_path.stem

    for fmt in formats:
        if fmt not in EXPORTERS:
            logger.warning("Format '%s' tidak didukung, skip.", fmt)
            continue
        out_file = output_dir / f"{stem}.{fmt}"
        EXPORTERS[fmt](result, out_file)
        exported_files.append(str(out_file))
        logger.info("Exported: %s", out_file)

    _notify(progress_callback, "Selesai!", 1.0)

    return {
        "input": str(input_path),
        "hash": file_hash,
        "cached": cached_data is not None,
        "duration": result.duration,
        "segments_count": len(result.segments),
        "exported_files": exported_files,
        "language": result.language,
        "engine": result.engine_name,
        "model": result.model_name,
    }


def run_batch(
    input_dir: str | Path,
    output_dir: str | Path = "output",
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Batch process semua file valid dalam folder.

    Args:
        input_dir: Folder berisi file audio/video.
        output_dir: Folder output.
        **kwargs: Parameter lain untuk run_pipeline.

    Returns:
        List hasil dari tiap file.
    """
    input_dir = Path(input_dir)
    results: list[dict[str, Any]] = []

    files = sorted(f for f in input_dir.iterdir() if f.is_file() and is_supported(f))
    logger.info("Batch: ditemukan %d file valid di %s", len(files), input_dir)

    for i, f in enumerate(files):
        logger.info("Batch [%d/%d]: %s", i + 1, len(files), f.name)
        try:
            r = run_pipeline(f, output_dir=output_dir, **kwargs)
            results.append(r)
        except Exception as e:
            logger.error("Gagal proses %s: %s", f.name, e)
            results.append({"input": str(f), "error": str(e)})

    return results


def _notify(callback: Callable[[str, float], None] | None, stage: str, progress: float) -> None:
    """Panggil progress callback kalau ada."""
    if callback:
        callback(stage, progress)
