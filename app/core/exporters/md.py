"""Exporter Markdown — format rapi dengan heading dan timestamp."""

from __future__ import annotations

from pathlib import Path

from app.core.engines.base import TranscriptResult


def export_md(result: TranscriptResult, output_path: str | Path) -> Path:
    """Export transkrip ke file .md.

    Args:
        result: Hasil transkrip.
        output_path: Path file output.

    Returns:
        Path ke file yang dibuat.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Transkrip Wawancara")
    lines.append("")
    lines.append(f"- **Bahasa**: {result.language}")
    lines.append(f"- **Durasi**: {_format_duration(result.duration)}")
    lines.append(f"- **Engine**: {result.engine_name}")
    lines.append(f"- **Model**: {result.model_name}")
    lines.append("")
    lines.append("---")
    lines.append("")

    current_speaker = ""
    for seg in result.segments:
        if seg.speaker and seg.speaker != current_speaker:
            lines.append(f"### {seg.speaker}")
            lines.append("")
            current_speaker = seg.speaker

        ts = _format_ts(seg.start, seg.end)
        lines.append(f"**{ts}** {seg.text}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _format_ts(start: float, end: float) -> str:
    return f"[{_sec(start)} → {_sec(end)}]"


def _sec(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def _format_duration(seconds: float) -> str:
    h, remainder = divmod(int(seconds), 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}j {m}m {s}d"
    return f"{m}m {s}d"
