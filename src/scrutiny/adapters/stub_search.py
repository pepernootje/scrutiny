"""Stub implementation of SearchAdapter for development and demo modes."""

from __future__ import annotations

import logging
import re

from scrutiny.adapters.base import SearchAdapter
from scrutiny.models import Chunk, MatchedChunk

logger = logging.getLogger(__name__)


class StubSearchAdapter(SearchAdapter):
    """Stub search adapter that works without Azure credentials.

    Parameters
    ----------
    demo_mode : bool
        When ``True``, returns the first ``demo_n`` chunks with a fixed score
        instead of running regex patterns.
    demo_n : int
        Number of chunks to return in demo mode.  Defaults to 3.
    """

    def __init__(self, demo_mode: bool = False, demo_n: int = 3) -> None:
        self._demo_mode = demo_mode
        self._demo_n = demo_n

    def search(
        self, chunks: list[Chunk], config: dict
    ) -> list[MatchedChunk]:
        """Search chunks using regex patterns or return demo results.

        In development mode, applies regex patterns from the config.
        Falls back to returning all chunks if no patterns are configured.
        In demo mode, returns the first ``demo_n`` chunks with score 0.85.

        Parameters
        ----------
        chunks : list of Chunk
            Candidate chunks to search.
        config : dict
            Parsed detection YAML configuration.

        Returns
        -------
        list of MatchedChunk
            Matched chunks with scores.
        """
        if self._demo_mode:
            logger.debug("Demo mode: returning first %d chunks", self._demo_n)
            return [
                MatchedChunk(chunk=c, score=0.85, engine="demo")
                for c in chunks[: self._demo_n]
            ]

        patterns = config.get("regex", {}).get("patterns", [])
        flags_str = config.get("regex", {}).get("flags", "")

        if not patterns:
            logger.warning(
                "No regex patterns configured; returning all %d chunks", len(chunks)
            )
            return [
                MatchedChunk(chunk=c, score=1.0, engine="regex") for c in chunks
            ]

        compiled_flags = _parse_flags(flags_str)
        matched: list[MatchedChunk] = []
        for chunk in chunks:
            for pattern in patterns:
                try:
                    if re.search(pattern, chunk.text, compiled_flags):
                        matched.append(
                            MatchedChunk(chunk=chunk, score=1.0, engine="regex")
                        )
                        break
                except re.error as exc:
                    logger.error("Invalid regex pattern %r: %s", pattern, exc)

        logger.debug(
            "Regex search matched %d / %d chunks", len(matched), len(chunks)
        )
        return matched


def _parse_flags(flags_str: str) -> int:
    """Convert a pipe-separated flag string to a compiled re flags integer.

    Parameters
    ----------
    flags_str : str
        E.g. ``"IGNORECASE|MULTILINE"``.

    Returns
    -------
    int
        Bitwise OR of the requested ``re`` flag constants.
    """
    flag_map = {
        "IGNORECASE": re.IGNORECASE,
        "MULTILINE": re.MULTILINE,
        "DOTALL": re.DOTALL,
    }
    result = 0
    for part in flags_str.split("|"):
        part = part.strip()
        if part and part in flag_map:
            result |= flag_map[part]
    return result
