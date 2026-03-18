"""Data models for the scrutiny pipeline.

All data passed between pipeline steps uses these dataclasses.
Never use plain dicts between steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A span of text extracted from a document.

    Parameters
    ----------
    text : str
        The text content of the chunk.
    chunk_index : int
        Zero-based index of this chunk within the document.
    page_number : int or None
        Page number where the chunk originates, or None if not applicable.
    start_char : int
        Character offset of the start of the chunk in the full document text.
    end_char : int
        Character offset of the end of the chunk in the full document text.
    metadata : dict
        Arbitrary metadata attached to the chunk (e.g. section heading).
    """

    text: str
    chunk_index: int
    page_number: int | None
    start_char: int
    end_char: int
    metadata: dict = field(default_factory=dict)


@dataclass
class MatchedChunk:
    """A chunk that has been selected by the detection step.

    Parameters
    ----------
    chunk : Chunk
        The underlying chunk that was matched.
    score : float
        Relevance score in the range [0.0, 1.0].
        Regex matches always receive a score of 1.0.
    engine : str
        The detection engine that produced this match.
        One of ``"regex"``, ``"azure_ai_search"``, or ``"hybrid"``.
    """

    chunk: Chunk
    score: float
    engine: str


@dataclass
class ClassificationResult:
    """The result of classifying a matched chunk with an LLM.

    Parameters
    ----------
    matched_chunk : MatchedChunk
        The matched chunk that was classified.
    output_fields : dict of str to str
        Key-value pairs produced by the LLM.  Always includes at least
        ``"decision"`` (``"YES"`` or ``"NO"``) and ``"justification"``.
    model : str
        Name of the model used for classification.
    is_stub : bool
        ``True`` when the result was produced by a stub adapter rather
        than a real Azure OpenAI call.
    """

    matched_chunk: MatchedChunk
    output_fields: dict[str, str]
    model: str
    is_stub: bool
