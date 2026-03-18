"""Tests for scrutiny.models."""

import pytest

from scrutiny.models import Chunk, ClassificationResult, MatchedChunk


class TestChunk:
    def test_basic_fields(self):
        chunk = Chunk(
            text="hello world",
            chunk_index=0,
            page_number=1,
            start_char=0,
            end_char=11,
        )
        assert chunk.text == "hello world"
        assert chunk.chunk_index == 0
        assert chunk.page_number == 1
        assert chunk.start_char == 0
        assert chunk.end_char == 11
        assert chunk.metadata == {}

    def test_page_number_none(self):
        chunk = Chunk(
            text="text",
            chunk_index=0,
            page_number=None,
            start_char=0,
            end_char=4,
        )
        assert chunk.page_number is None

    def test_metadata(self):
        chunk = Chunk(
            text="text",
            chunk_index=0,
            page_number=None,
            start_char=0,
            end_char=4,
            metadata={"section": "intro"},
        )
        assert chunk.metadata == {"section": "intro"}


class TestMatchedChunk:
    def test_fields(self):
        chunk = Chunk(
            text="text", chunk_index=0, page_number=None, start_char=0, end_char=4
        )
        mc = MatchedChunk(chunk=chunk, score=1.0, engine="regex")
        assert mc.chunk is chunk
        assert mc.score == 1.0
        assert mc.engine == "regex"


class TestClassificationResult:
    def test_fields(self):
        chunk = Chunk(
            text="text", chunk_index=0, page_number=None, start_char=0, end_char=4
        )
        mc = MatchedChunk(chunk=chunk, score=1.0, engine="regex")
        result = ClassificationResult(
            matched_chunk=mc,
            output_fields={"decision": "YES", "justification": "relevant"},
            model="stub-model",
            is_stub=True,
        )
        assert result.output_fields["decision"] == "YES"
        assert result.is_stub is True
        assert result.model == "stub-model"
