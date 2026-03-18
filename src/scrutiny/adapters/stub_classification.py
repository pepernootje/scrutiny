"""Stub implementation of ClassificationAdapter for development and demo modes."""

from __future__ import annotations

import logging

from scrutiny.adapters.base import ClassificationAdapter
from scrutiny.models import ClassificationResult, MatchedChunk

logger = logging.getLogger(__name__)

_DEV_KEYWORDS = [
    "risk",
    "disclose",
    "material",
    "conflict",
    "fee",
    "commission",
    "interest",
]


class StubClassificationAdapter(ClassificationAdapter):
    """Stub classification adapter that works without Azure credentials.

    Parameters
    ----------
    demo_mode : bool
        When ``True``, the first chunk is always YES and the rest NO.
        When ``False``, uses a simple keyword heuristic.
    """

    def __init__(self, demo_mode: bool = False) -> None:
        self._demo_mode = demo_mode

    def classify(
        self, matched_chunks: list[MatchedChunk], config: dict
    ) -> list[ClassificationResult]:
        """Classify matched chunks using a stub heuristic.

        Parameters
        ----------
        matched_chunks : list of MatchedChunk
            Chunks to classify.
        config : dict
            Parsed classification YAML configuration.

        Returns
        -------
        list of ClassificationResult
            One stub result per matched chunk.
        """
        model = config.get("model", "stub-model")
        output_fields_keys = config.get(
            "output_fields", ["decision", "justification"]
        )
        results: list[ClassificationResult] = []

        for i, mc in enumerate(matched_chunks):
            if self._demo_mode:
                decision = "YES" if i == 0 else "NO"
                justification = (
                    f'Chunk text: "{mc.chunk.text[:80]}..."'
                    if len(mc.chunk.text) > 80
                    else f'Chunk text: "{mc.chunk.text}"'
                )
            else:
                text_lower = mc.chunk.text.lower()
                decision = (
                    "YES"
                    if any(kw in text_lower for kw in _DEV_KEYWORDS)
                    else "NO"
                )
                justification = (
                    f"[Dev mode] Keyword heuristic applied. Decision: {decision}."
                )

            output: dict[str, str] = {}
            for field in output_fields_keys:
                if field == "decision":
                    output["decision"] = decision
                elif field == "justification":
                    output["justification"] = justification
                else:
                    output[field] = f"[stub] {field} not available in stub mode"

            results.append(
                ClassificationResult(
                    matched_chunk=mc,
                    output_fields=output,
                    model=model,
                    is_stub=True,
                )
            )
            logger.debug(
                "Stub classified chunk %d as %s", mc.chunk.chunk_index, decision
            )

        return results
