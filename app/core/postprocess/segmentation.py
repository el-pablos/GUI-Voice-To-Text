"""Post-processing segmentasi — mode timestamp dan heuristic diarization."""

from __future__ import annotations

from app.core.engines.base import Segment, TranscriptResult


def segments_per_sentence(result: TranscriptResult) -> list[Segment]:
    """Kembalikan segmen apa adanya (per kalimat dari engine)."""
    return list(result.segments)


def segments_merged(result: TranscriptResult, gap_threshold: float = 1.0) -> list[Segment]:
    """Gabung segmen yang berdekatan (gap < threshold) jadi satu segmen lebih besar.

    Args:
        result: Hasil transkrip.
        gap_threshold: Jeda maksimum (detik) untuk digabung.

    Returns:
        List segmen yang sudah di-merge.
    """
    if not result.segments:
        return []

    merged: list[Segment] = []
    current = Segment(
        start=result.segments[0].start,
        end=result.segments[0].end,
        text=result.segments[0].text,
        speaker=result.segments[0].speaker,
    )

    for seg in result.segments[1:]:
        gap = seg.start - current.end
        if gap <= gap_threshold and seg.speaker == current.speaker:
            # Gabung
            current.end = seg.end
            current.text = f"{current.text} {seg.text}"
        else:
            merged.append(current)
            current = Segment(
                start=seg.start,
                end=seg.end,
                text=seg.text,
                speaker=seg.speaker,
            )

    merged.append(current)
    return merged


def heuristic_diarization(result: TranscriptResult, silence_gap: float = 2.0) -> TranscriptResult:
    """Heuristic diarization sederhana berdasarkan jeda panjang.

    Bukan diarization sesungguhnya — hanya memisahkan speaker berdasarkan
    silence gap yang panjang (asumsi: jeda panjang = ganti speaker).

    Args:
        result: Hasil transkrip tanpa speaker label.
        silence_gap: Jeda minimal (detik) untuk dianggap ganti speaker.

    Returns:
        TranscriptResult dengan speaker label heuristic.
    """
    if not result.segments:
        return result

    speaker_idx = 1
    labeled: list[Segment] = []

    for i, seg in enumerate(result.segments):
        if i == 0:
            speaker_label = f"Speaker {speaker_idx}"
        else:
            gap = seg.start - result.segments[i - 1].end
            if gap >= silence_gap:
                speaker_idx += 1
                speaker_label = f"Speaker {speaker_idx}"
            else:
                speaker_label = labeled[-1].speaker

        labeled.append(
            Segment(
                start=seg.start,
                end=seg.end,
                text=seg.text,
                speaker=speaker_label,
                confidence=seg.confidence,
            )
        )

    return TranscriptResult(
        segments=labeled,
        language=result.language,
        duration=result.duration,
        engine_name=result.engine_name,
        model_name=result.model_name,
        metadata={**result.metadata, "diarization": "heuristic"},
    )
