"""Tests for scrutiny.chunking."""

import pytest

from scrutiny.chunking import chunk_document
from scrutiny.models import Chunk

_SAMPLE_TEXT = (
    "The fund charges a management fee of 1.5%. "
    "There may be conflicts of interest between the manager and investors. "
    "Investors should be aware of all material risks.\n\n"
    "Past performance does not guarantee future results. "
    "The fund may invest in illiquid assets."
)


class TestChunkDocument:
    def test_paragraph_method(self):
        config = {"method": "paragraph", "chunk_size": 500, "overlap": 0}
        chunks = chunk_document(_SAMPLE_TEXT, config)
        assert isinstance(chunks, list)
        assert all(isinstance(c, Chunk) for c in chunks)
        assert len(chunks) >= 2  # two paragraphs

    def test_sentence_method(self):
        config = {"method": "sentence", "chunk_size": 500, "overlap": 0}
        chunks = chunk_document(_SAMPLE_TEXT, config)
        assert len(chunks) >= 2

    def test_token_window_method(self):
        config = {"method": "token_window", "chunk_size": 10, "overlap": 2}
        chunks = chunk_document(_SAMPLE_TEXT, config)
        assert len(chunks) >= 2

    def test_token_window_overlap_less_than_chunk_size(self):
        """Overlap must be less than chunk_size to avoid infinite loops."""
        config = {"method": "token_window", "chunk_size": 5, "overlap": 5}
        # Should not hang or raise
        chunks = chunk_document(_SAMPLE_TEXT, config)
        assert len(chunks) >= 1

    def test_regex_boundary_method(self):
        config = {
            "method": "regex_boundary",
            "chunk_size": 500,
            "overlap": 0,
            "boundary_pattern": r"\n{2,}",
        }
        chunks = chunk_document(_SAMPLE_TEXT, config)
        assert len(chunks) >= 2

    def test_invalid_method_raises_value_error(self):
        config = {"method": "invalid_method"}
        with pytest.raises(ValueError, match="Chunking method must be one of"):
            chunk_document(_SAMPLE_TEXT, config)

    def test_invalid_regex_boundary_raises_value_error(self):
        config = {
            "method": "regex_boundary",
            "boundary_pattern": "[invalid",
        }
        with pytest.raises(ValueError, match="Invalid boundary_pattern"):
            chunk_document(_SAMPLE_TEXT, config)

    def test_chunks_have_correct_indices(self):
        config = {"method": "paragraph", "chunk_size": 500, "overlap": 0}
        chunks = chunk_document(_SAMPLE_TEXT, config)
        for i, c in enumerate(chunks):
            assert c.chunk_index == i

    def test_empty_text(self):
        config = {"method": "paragraph", "chunk_size": 500, "overlap": 0}
        chunks = chunk_document("", config)
        assert chunks == []

    def test_whitespace_only_text(self):
        config = {"method": "paragraph", "chunk_size": 500, "overlap": 0}
        chunks = chunk_document("   \n\n   ", config)
        assert chunks == []

    def test_chunk_start_end_chars(self):
        config = {"method": "paragraph", "chunk_size": 500, "overlap": 0}
        chunks = chunk_document(_SAMPLE_TEXT, config)
        for c in chunks:
            assert c.start_char >= 0
            assert c.end_char > c.start_char
            assert c.end_char <= len(_SAMPLE_TEXT) + 1  # +1 for possible trailing \n
