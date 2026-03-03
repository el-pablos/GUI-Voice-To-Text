"""Exporter JSON — detail segmen lengkap."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.engines.base import TranscriptResult


def export_json(result: TranscriptResult, output_path: str | Path) -> Path:
    """Export transkrip ke file .json (detail lengkap).

    Args:
        result: Hasil transkrip.
        output_path: Path file output.

    Returns:
        Path ke file yang dibuat.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = result.to_dict()
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path
