"""Tests for scrutiny adapter implementations."""

import pytest

from scrutiny.adapters.stub_classification import StubClassificationAdapter
from scrutiny.adapters.stub_search import StubSearchAdapter, _parse_flags
from scrutiny.models import Chunk, MatchedChunk
import re

_CHUNKS = [
    Chunk(
        text="The fund charges a management fee of 1.5%.",
        chunk_index=0,
        page_number=1,
        start_char=0,
        end_char=42,
    ),
    Chunk(
        text="Conflict of interest disclosures are required.",
        chunk_index=1,
        page_number=2,
        start_char=43,
        end_char=89,
    ),
]

_MATCHED = [
    MatchedChunk(chunk=_CHUNKS[0], score=1.0, engine="regex"),
]

_CLASSIF_CONFIG = {
    "adapter": "azure_openai",
    "model": "stub-model",
    "temperature": 0.0,
    "prompt_template": "{{ chunk }}",
    "output_fields": ["decision", "justification"],
}


class TestStubSearchAdapterDevMode:
    def test_regex_match(self):
        adapter = StubSearchAdapter()
        config = {
            "engine": "regex",
            "regex": {"patterns": ["conflict"], "flags": "IGNORECASE"},
        }
        matched = adapter.search(_CHUNKS, config)
        assert len(matched) == 1
        assert matched[0].chunk.chunk_index == 1
        assert matched[0].score == 1.0
        assert matched[0].engine == "regex"

    def test_no_patterns_returns_all(self):
        adapter = StubSearchAdapter()
        config = {"engine": "regex", "regex": {"patterns": [], "flags": ""}}
        matched = adapter.search(_CHUNKS, config)
        assert len(matched) == len(_CHUNKS)

    def test_invalid_regex_skipped(self):
        adapter = StubSearchAdapter()
        config = {
            "engine": "regex",
            "regex": {"patterns": ["[invalid"], "flags": ""},
        }
        # Should not raise; skips the bad pattern
        matched = adapter.search(_CHUNKS, config)
        assert matched == []

    def test_case_insensitive_flag(self):
        adapter = StubSearchAdapter()
        config = {
            "engine": "regex",
            "regex": {"patterns": ["CONFLICT"], "flags": "IGNORECASE"},
        }
        matched = adapter.search(_CHUNKS, config)
        assert len(matched) == 1


class TestStubSearchAdapterDemoMode:
    def test_demo_returns_first_n(self):
        adapter = StubSearchAdapter(demo_mode=True, demo_n=1)
        matched = adapter.search(_CHUNKS, {})
        assert len(matched) == 1
        assert matched[0].score == pytest.approx(0.85)
        assert matched[0].engine == "demo"

    def test_demo_n_exceeds_chunks(self):
        adapter = StubSearchAdapter(demo_mode=True, demo_n=100)
        matched = adapter.search(_CHUNKS, {})
        assert len(matched) == len(_CHUNKS)


class TestParseFlags:
    def test_ignorecase(self):
        assert _parse_flags("IGNORECASE") == re.IGNORECASE

    def test_multiple_flags(self):
        flags = _parse_flags("IGNORECASE|MULTILINE")
        assert flags & re.IGNORECASE
        assert flags & re.MULTILINE

    def test_empty_string(self):
        assert _parse_flags("") == 0

    def test_unknown_flag_ignored(self):
        assert _parse_flags("UNKNOWN_FLAG") == 0


class TestStubClassificationAdapterDevMode:
    def test_keyword_yes(self):
        adapter = StubClassificationAdapter(demo_mode=False)
        results = adapter.classify(_MATCHED, _CLASSIF_CONFIG)
        # "fee" is a keyword
        assert results[0].output_fields["decision"] == "YES"

    def test_dev_mode_justification_prefix(self):
        adapter = StubClassificationAdapter(demo_mode=False)
        results = adapter.classify(_MATCHED, _CLASSIF_CONFIG)
        assert "[Dev mode]" in results[0].output_fields["justification"]

    def test_is_stub_true(self):
        adapter = StubClassificationAdapter()
        results = adapter.classify(_MATCHED, _CLASSIF_CONFIG)
        assert all(r.is_stub for r in results)

    def test_model_from_config(self):
        adapter = StubClassificationAdapter()
        results = adapter.classify(_MATCHED, _CLASSIF_CONFIG)
        assert results[0].model == "stub-model"

    def test_extra_output_fields(self):
        config = dict(_CLASSIF_CONFIG, output_fields=["decision", "justification", "severity"])
        adapter = StubClassificationAdapter()
        results = adapter.classify(_MATCHED, config)
        assert "severity" in results[0].output_fields
        assert "[stub]" in results[0].output_fields["severity"]


class TestStubClassificationAdapterDemoMode:
    def test_first_yes_rest_no(self):
        matched = [
            MatchedChunk(chunk=_CHUNKS[0], score=1.0, engine="demo"),
            MatchedChunk(chunk=_CHUNKS[1], score=0.85, engine="demo"),
        ]
        adapter = StubClassificationAdapter(demo_mode=True)
        results = adapter.classify(matched, _CLASSIF_CONFIG)
        assert results[0].output_fields["decision"] == "YES"
        assert results[1].output_fields["decision"] == "NO"

    def test_chunk_text_quoted_in_justification(self):
        adapter = StubClassificationAdapter(demo_mode=True)
        results = adapter.classify(_MATCHED, _CLASSIF_CONFIG)
        assert "Chunk text:" in results[0].output_fields["justification"]
