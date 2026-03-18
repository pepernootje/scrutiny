"""Classification module.

Evaluates matched chunks against an LLM prompt template.
"""

from __future__ import annotations

import logging

from scrutiny.adapters.base import ClassificationAdapter
from scrutiny.models import ClassificationResult, MatchedChunk

logger = logging.getLogger(__name__)

_VALID_ADAPTERS = {"azure_openai"}
_REQUIRED_OUTPUT_FIELDS = {"decision", "justification"}


def run_classification(
    matched_chunks: list[MatchedChunk],
    config: dict,
    adapter: ClassificationAdapter,
) -> list[ClassificationResult]:
    """Run the classification step on matched chunks.

    Validates the classification config, then delegates to
    ``adapter.classify()``.

    Parameters
    ----------
    matched_chunks : list of MatchedChunk
        Chunks from the detection step.
    config : dict
        Parsed classification YAML configuration.
    adapter : ClassificationAdapter
        Classification adapter to use.

    Returns
    -------
    list of ClassificationResult
        One result per matched chunk.

    Raises
    ------
    ValueError
        If the config is invalid.
    """
    adapter_name = config.get("adapter", "")
    if adapter_name not in _VALID_ADAPTERS:
        raise ValueError(
            f"Classification adapter must be one of: "
            f"{', '.join(sorted(_VALID_ADAPTERS))}. Got: {adapter_name!r}"
        )

    output_fields = config.get("output_fields", [])
    missing = _REQUIRED_OUTPUT_FIELDS - set(output_fields)
    if missing:
        raise ValueError(
            f"output_fields must include: {', '.join(sorted(missing))}"
        )

    if "{{ chunk }}" not in config.get("prompt_template", ""):
        raise ValueError(
            "prompt_template must contain the placeholder {{ chunk }}"
        )

    logger.debug(
        "run_classification: adapter=%s, %d chunks input",
        adapter_name,
        len(matched_chunks),
    )
    results = adapter.classify(matched_chunks, config)
    logger.debug("run_classification: %d results produced", len(results))
    return results
