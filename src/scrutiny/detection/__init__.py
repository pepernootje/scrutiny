"""Detection module.

Filters chunks produced by the chunking step using a search adapter.
"""

from __future__ import annotations

import logging

from scrutiny.adapters.base import SearchAdapter
from scrutiny.models import Chunk, MatchedChunk

logger = logging.getLogger(__name__)

_VALID_ENGINES = {"regex", "azure_ai_search", "hybrid"}


def run_detection(
    chunks: list[Chunk],
    config: dict,
    adapter: SearchAdapter,
) -> list[MatchedChunk]:
    """Run the detection step on a list of chunks.

    Validates the detection config, then delegates to ``adapter.search()``.

    Parameters
    ----------
    chunks : list of Chunk
        Chunks from the chunking step.
    config : dict
        Parsed detection YAML configuration.
    adapter : SearchAdapter
        Search adapter to use for matching.

    Returns
    -------
    list of MatchedChunk
        Chunks that passed the detection filter.

    Raises
    ------
    ValueError
        If the config is invalid (e.g. unknown engine).
    """
    engine = config.get("engine", "")
    if engine not in _VALID_ENGINES:
        raise ValueError(
            f"Detection engine must be one of: "
            f"{', '.join(sorted(_VALID_ENGINES))}. Got: {engine!r}"
        )

    logger.debug(
        "run_detection: engine=%s, %d chunks input", engine, len(chunks)
    )
    matched = adapter.search(chunks, config)
    logger.debug("run_detection: %d chunks matched", len(matched))
    return matched
