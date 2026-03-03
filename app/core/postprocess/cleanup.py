"""Post-processing cleanup — normalisasi teks hasil STT."""

from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    """Normalisasi spasi: multiple spaces → single, trim."""
    return re.sub(r"\s+", " ", text).strip()


def remove_noise_tokens(text: str) -> str:
    """Hapus noise token yang jelas dari Whisper (musik, applause, dll)."""
    # Pattern: [Music], [Applause], (noise), *music*, dll
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\*.*?\*", "", text)
    return normalize_whitespace(text)


# Filler words Indonesia/English
FILLER_PATTERNS = [
    r"\b[eé]+[eh]*\b",     # eee, eeh
    r"\banu\b",             # anu
    r"\bem+\b",             # emm, em
    r"\bhmm+\b",            # hmm
    r"\buh+m*\b",           # uh, uhm
    r"\bum+\b",             # um, umm
    r"\byaa+\b",            # yaaa
    r"\bnah+\b",            # nah, nahh
    r"\bgitu\s+sih\b",     # gitu sih (sering noise di Indonesia)
]

_FILLER_RE = re.compile("|".join(FILLER_PATTERNS), re.IGNORECASE)


def remove_fillers(text: str) -> str:
    """Hapus filler words (opsional — bisa dimatikan user).

    Args:
        text: Teks input.

    Returns:
        Teks tanpa filler.
    """
    text = _FILLER_RE.sub("", text)
    return normalize_whitespace(text)


def cleanup_text(text: str, remove_filler: bool = False) -> str:
    """Pipeline cleanup lengkap.

    Args:
        text: Teks mentah dari STT.
        remove_filler: Apakah filler words dihapus.

    Returns:
        Teks yang sudah dibersihkan.
    """
    text = remove_noise_tokens(text)
    if remove_filler:
        text = remove_fillers(text)
    text = normalize_whitespace(text)
    return text
