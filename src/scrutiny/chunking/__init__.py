"""Document chunking module.

Splits document text into candidate spans using one of four methods:
sentence, paragraph, token_window, or regex_boundary.
"""

from __future__ import annotations

import logging
import re

from scrutiny.models import Chunk

logger = logging.getLogger(__name__)

_VALID_METHODS = {"sentence", "paragraph", "token_window", "regex_boundary"}

# Simple sentence-ending pattern (handles common abbreviations poorly on purpose
# — this is a heuristic for the playground, not a production NLP pipeline).
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def chunk_document(text: str, config: dict) -> list[Chunk]:
    """Split document text into chunks according to the chunking config.

    Parameters
    ----------
    text : str
        Full document text to split.
    config : dict
        Parsed chunking YAML configuration.  Must contain at least ``method``.

    Returns
    -------
    list of Chunk
        Ordered list of chunks produced from ``text``.

    Raises
    ------
    ValueError
        If ``method`` is missing or not one of the allowed values.
    """
    method = config.get("method", "")
    if method not in _VALID_METHODS:
        raise ValueError(
            f"Chunking method must be one of: "
            f"{', '.join(sorted(_VALID_METHODS))}. Got: {method!r}"
        )

    chunk_size = int(config.get("chunk_size", 500))
    overlap = int(config.get("overlap", 0))
    boundary_pattern = config.get("boundary_pattern", r"\n{2,}")

    match method:
        case "sentence":
            spans = _split_sentences(text)
        case "paragraph":
            spans = _split_paragraphs(text)
        case "token_window":
            spans = _split_token_window(text, chunk_size, overlap)
        case "regex_boundary":
            spans = _split_regex_boundary(text, boundary_pattern)
        case _:  # pragma: no cover — exhaustive match
            spans = []

    chunks = [
        Chunk(
            text=span_text,
            chunk_index=i,
            page_number=None,
            start_char=start,
            end_char=end,
        )
        for i, (span_text, start, end) in enumerate(spans)
        if span_text.strip()
    ]

    logger.debug(
        "chunk_document: method=%s produced %d chunks from %d chars",
        method,
        len(chunks),
        len(text),
    )
    return chunks


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _split_sentences(text: str) -> list[tuple[str, int, int]]:
    """Split text at sentence boundaries.

    Parameters
    ----------
    text : str
        Input text.

    Returns
    -------
    list of (str, int, int)
        Tuples of (span_text, start_char, end_char).
    """
    boundaries = [0] + [m.end() for m in _SENTENCE_RE.finditer(text)]
    spans = []
    for i, start in enumerate(boundaries):
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
        span = text[start:end]
        spans.append((span, start, end))
    return spans


def _split_paragraphs(text: str) -> list[tuple[str, int, int]]:
    """Split text at blank-line boundaries (paragraphs).

    Parameters
    ----------
    text : str
        Input text.

    Returns
    -------
    list of (str, int, int)
        Tuples of (span_text, start_char, end_char).
    """
    return _split_regex_boundary(text, r"\n{2,}")


def _split_token_window(
    text: str, chunk_size: int, overlap: int
) -> list[tuple[str, int, int]]:
    """Split text into overlapping word-count windows.

    Parameters
    ----------
    text : str
        Input text.
    chunk_size : int
        Approximate number of words per chunk.
    overlap : int
        Number of words to repeat at the start of each subsequent chunk.

    Returns
    -------
    list of (str, int, int)
        Tuples of (span_text, start_char, end_char).
    """
    if chunk_size <= 0:
        chunk_size = 500
    if overlap < 0:
        overlap = 0
    overlap = min(overlap, chunk_size - 1)

    # Tokenise on whitespace; track char positions
    word_positions: list[tuple[str, int, int]] = []
    for m in re.finditer(r"\S+", text):
        word_positions.append((m.group(), m.start(), m.end()))

    if not word_positions:
        return []

    spans: list[tuple[str, int, int]] = []
    step = max(1, chunk_size - overlap)
    i = 0
    while i < len(word_positions):
        window = word_positions[i : i + chunk_size]
        span_text = text[window[0][1] : window[-1][2]]
        spans.append((span_text, window[0][1], window[-1][2]))
        i += step

    return spans


def _split_regex_boundary(
    text: str, pattern: str
) -> list[tuple[str, int, int]]:
    """Split text at positions matched by a regex pattern.

    Parameters
    ----------
    text : str
        Input text.
    pattern : str
        Regex pattern to split on (e.g. ``r"\\n{2,}"``).

    Returns
    -------
    list of (str, int, int)
        Tuples of (span_text, start_char, end_char).

    Raises
    ------
    ValueError
        If ``pattern`` is not a valid regular expression.
    """
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise ValueError(
            f"Invalid boundary_pattern {pattern!r}: {exc}"
        ) from exc

    boundaries = [0]
    for m in compiled.finditer(text):
        boundaries.append(m.end())
    boundaries.append(len(text))

    spans = []
    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]
        span = text[start:end]
        spans.append((span, start, end))
    return spans
