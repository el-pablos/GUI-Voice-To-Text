"""Exporter TXT — teks polos dari hasil transkrip."""

from __future__ import annotations

from pathlib import Path

from app.core.engines.base import TranscriptResult


def export_txt(result: TranscriptResult, output_path: str | Path) -> Path:
    """Export transkrip ke file .txt (teks polos dengan timestamp).

    Args:
        result: Hasil transkrip.
        output_path: Path file output.

    Returns:
        Path ke file yang dibuat.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    for seg in result.segments:
        ts = _format_ts(seg.start)
        speaker = f"[{seg.speaker}] " if seg.speaker else ""
        lines.append(f"[{ts}] {speaker}{seg.text}")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _format_ts(seconds: float) -> str:
    """Format detik ke MM:SS."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"
