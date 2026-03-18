"""Abstract base classes for search and classification adapters.

Every real and stub implementation must subclass these exactly.
No extra public methods should be added.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from scrutiny.models import Chunk, ClassificationResult, MatchedChunk


class SearchAdapter(ABC):
    """Abstract base class for chunk detection adapters.

    Parameters
    ----------
    None
    """

    @abstractmethod
    def search(
        self, chunks: list[Chunk], config: dict
    ) -> list[MatchedChunk]:
        """Search chunks and return those that match the detection criteria.

        Parameters
        ----------
        chunks : list of Chunk
            Candidate chunks produced by the chunking step.
        config : dict
            Parsed detection YAML configuration.

        Returns
        -------
        list of MatchedChunk
            Chunks selected by this adapter, with relevance scores.
        """


class ClassificationAdapter(ABC):
    """Abstract base class for LLM classification adapters.

    Parameters
    ----------
    None
    """

    @abstractmethod
    def classify(
        self, matched_chunks: list[MatchedChunk], config: dict
    ) -> list[ClassificationResult]:
        """Classify matched chunks using an LLM.

        Parameters
        ----------
        matched_chunks : list of MatchedChunk
            Chunks produced by the detection step.
        config : dict
            Parsed classification YAML configuration.

        Returns
        -------
        list of ClassificationResult
            One result per matched chunk.
        """
