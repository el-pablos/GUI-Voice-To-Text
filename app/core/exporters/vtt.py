"""Exporter VTT — format subtitle WebVTT."""

from __future__ import annotations

from pathlib import Path

from app.core.engines.base import TranscriptResult


def export_vtt(result: TranscriptResult, output_path: str | Path) -> Path:
    """Export transkrip ke file .vtt (WebVTT subtitle).

    Args:
        result: Hasil transkrip.
        output_path: Path file output.

    Returns:
        Path ke file yang dibuat.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = ["WEBVTT", ""]
    for i, seg in enumerate(result.segments, 1):
        lines.append(str(i))
        lines.append(f"{_vtt_time(seg.start)} --> {_vtt_time(seg.end)}")
        speaker = f"<v {seg.speaker}>" if seg.speaker else ""
        lines.append(f"{speaker}{seg.text}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _vtt_time(seconds: float) -> str:
    """Format detik ke HH:MM:SS.mmm (format VTT)."""
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    ms = int((s % 1) * 1000)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}.{ms:03d}"
