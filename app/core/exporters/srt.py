"""Exporter SRT — format subtitle SubRip."""

from __future__ import annotations

from pathlib import Path

from app.core.engines.base import TranscriptResult


def export_srt(result: TranscriptResult, output_path: str | Path) -> Path:
    """Export transkrip ke file .srt (SubRip subtitle).

    Args:
        result: Hasil transkrip.
        output_path: Path file output.

    Returns:
        Path ke file yang dibuat.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    for i, seg in enumerate(result.segments, 1):
        lines.append(str(i))
        lines.append(f"{_srt_time(seg.start)} --> {_srt_time(seg.end)}")
        speaker = f"[{seg.speaker}] " if seg.speaker else ""
        lines.append(f"{speaker}{seg.text}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _srt_time(seconds: float) -> str:
    """Format detik ke HH:MM:SS,mmm (format SRT)."""
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    ms = int((s % 1) * 1000)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"
