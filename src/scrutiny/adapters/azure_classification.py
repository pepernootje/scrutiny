"""Azure OpenAI classification adapter."""

from __future__ import annotations

import logging
import re

from scrutiny.adapters.base import ClassificationAdapter
from scrutiny.models import ClassificationResult, MatchedChunk

logger = logging.getLogger(__name__)


class AzureClassificationAdapter(ClassificationAdapter):
    """Classification adapter backed by Azure OpenAI.

    Azure SDK classes are imported lazily inside methods to avoid top-level
    import errors when credentials are not configured.

    Parameters
    ----------
    endpoint : str
        Azure OpenAI service endpoint URL.
    api_key : str
        Azure OpenAI API key.
    api_version : str
        Azure OpenAI API version string (e.g. ``"2024-02-01"``).
    """

    def __init__(
        self, endpoint: str, api_key: str, api_version: str = "2024-02-01"
    ) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._api_version = api_version

    def classify(
        self, matched_chunks: list[MatchedChunk], config: dict
    ) -> list[ClassificationResult]:
        """Classify matched chunks using Azure OpenAI.

        Parameters
        ----------
        matched_chunks : list of MatchedChunk
            Chunks to classify.
        config : dict
            Parsed classification YAML configuration.

        Returns
        -------
        list of ClassificationResult
            One result per matched chunk.

        Raises
        ------
        RuntimeError
            If the Azure OpenAI call fails.
        """
        from openai import AzureOpenAI  # noqa: PLC0415

        model = config.get("model", "gpt-4")
        temperature = config.get("temperature", 0.0)
        prompt_template = config.get("prompt_template", "{{ chunk }}")
        output_fields_keys = config.get(
            "output_fields", ["decision", "justification"]
        )
        topic = config.get("topic", "")

        try:
            client = AzureOpenAI(
                azure_endpoint=self._endpoint,
                api_key=self._api_key,
                api_version=self._api_version,
            )
        except Exception as exc:
            logger.error("Failed to create Azure OpenAI client: %s", exc)
            raise RuntimeError(
                "Could not connect to Azure OpenAI. "
                "Check your credentials and try again."
            ) from exc

        results: list[ClassificationResult] = []
        for mc in matched_chunks:
            prompt = prompt_template.replace(
                "{{ chunk }}", mc.chunk.text
            ).replace("{{ topic }}", topic)

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                )
                raw = response.choices[0].message.content or ""
            except Exception as exc:
                logger.error(
                    "Azure OpenAI call failed for chunk %d: %s",
                    mc.chunk.chunk_index,
                    exc,
                )
                raise RuntimeError(
                    "Could not connect to Azure OpenAI. "
                    "Check your credentials and try again."
                ) from exc

            output = _parse_output(raw, output_fields_keys)
            results.append(
                ClassificationResult(
                    matched_chunk=mc,
                    output_fields=output,
                    model=model,
                    is_stub=False,
                )
            )
            logger.debug(
                "Classified chunk %d: %s",
                mc.chunk.chunk_index,
                output.get("decision"),
            )

        return results


def _parse_output(raw: str, fields: list[str]) -> dict[str, str]:
    """Parse LLM output into a dict of field name to value.

    Expects lines like ``FIELD: value`` in the LLM response.

    Parameters
    ----------
    raw : str
        Raw LLM response text.
    fields : list of str
        Expected output field names.

    Returns
    -------
    dict of str to str
        Parsed field values. Missing fields default to an empty string.
    """
    output: dict[str, str] = {f: "" for f in fields}
    for field in fields:
        pattern = re.compile(
            rf"^{re.escape(field.upper())}[:\s]+(.+)$", re.MULTILINE | re.IGNORECASE
        )
        match = pattern.search(raw)
        if match:
            output[field] = match.group(1).strip()
    if not output.get("decision"):
        if "yes" in raw.lower():
            output["decision"] = "YES"
        elif "no" in raw.lower():
            output["decision"] = "NO"
    if not output.get("justification"):
        output["justification"] = raw.strip()
    return output
