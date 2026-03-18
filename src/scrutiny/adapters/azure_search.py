"""Azure AI Search adapter for chunk detection."""

from __future__ import annotations

import logging

from scrutiny.adapters.base import SearchAdapter
from scrutiny.models import Chunk, MatchedChunk

logger = logging.getLogger(__name__)


class AzureSearchAdapter(SearchAdapter):
    """Search adapter backed by Azure AI Search.

    Azure SDK classes are imported lazily inside methods to avoid top-level
    import errors when credentials are not configured.

    Parameters
    ----------
    endpoint : str
        Azure AI Search service endpoint URL.
    credential : object
        An Azure credential object (e.g. ``DefaultAzureCredential``).
    """

    def __init__(self, endpoint: str, credential: object) -> None:
        self._endpoint = endpoint
        self._credential = credential

    def search(
        self, chunks: list[Chunk], config: dict
    ) -> list[MatchedChunk]:
        """Search using Azure AI Search.

        Parameters
        ----------
        chunks : list of Chunk
            Candidate chunks to search.
        config : dict
            Parsed detection YAML configuration.

        Returns
        -------
        list of MatchedChunk
            Chunks matched by Azure AI Search, with relevance scores.

        Raises
        ------
        RuntimeError
            If the Azure AI Search call fails.
        """
        from azure.search.documents import SearchClient  # noqa: PLC0415

        index_name = config.get("azure_ai_search", {}).get("index_name", "")
        query = config.get("azure_ai_search", {}).get("query", "")
        top_k = config.get("azure_ai_search", {}).get("top_k", 10)

        try:
            client = SearchClient(
                endpoint=self._endpoint,
                index_name=index_name,
                credential=self._credential,  # type: ignore[arg-type]
            )
            az_results = client.search(search_text=query, top=top_k)
            matched_ids = {
                r.get("id"): r.get("@search.score", 0.0) for r in az_results
            }
        except Exception as exc:
            logger.error("Azure AI Search call failed: %s", exc)
            raise RuntimeError(
                "Could not connect to Azure AI Search. "
                "Check your credentials and try again."
            ) from exc

        matched: list[MatchedChunk] = []
        for chunk in chunks:
            chunk_id = str(chunk.chunk_index)
            if chunk_id in matched_ids:
                raw_score = matched_ids[chunk_id]
                score = min(1.0, max(0.0, float(raw_score)))
                matched.append(
                    MatchedChunk(chunk=chunk, score=score, engine="azure_ai_search")
                )

        logger.debug("Azure AI Search matched %d chunks", len(matched))
        return matched
