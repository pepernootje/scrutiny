"""Tests for scrutiny.detection."""

import pytest

from scrutiny.adapters.stub_search import StubSearchAdapter
from scrutiny.detection import run_detection
from scrutiny.models import Chunk, MatchedChunk

_CHUNKS = [
    Chunk(
        text="The fund charges a management fee of 1.5%.",
        chunk_index=0,
        page_number=1,
        start_char=0,
        end_char=42,
    ),
    Chunk(
        text="There may be conflicts of interest between the manager.",
        chunk_index=1,
        page_number=1,
        start_char=43,
        end_char=97,
    ),
    Chunk(
        text="Past performance does not guarantee future results.",
        chunk_index=2,
        page_number=2,
        start_char=98,
        end_char=148,
    ),
]


class TestRunDetection:
    def test_regex_engine_matches(self):
        config = {
            "engine": "regex",
            "regex": {
                "patterns": ["conflict"],
                "flags": "IGNORECASE",
            },
        }
        adapter = StubSearchAdapter()
        matched = run_detection(_CHUNKS, config, adapter)
        assert len(matched) == 1
        assert matched[0].chunk.chunk_index == 1

    def test_regex_engine_no_match(self):
        config = {
            "engine": "regex",
            "regex": {
                "patterns": ["nonexistent_xyz"],
                "flags": "",
            },
        }
        adapter = StubSearchAdapter()
        matched = run_detection(_CHUNKS, config, adapter)
        assert matched == []

    def test_no_patterns_returns_all_chunks(self):
        config = {
            "engine": "regex",
            "regex": {"patterns": [], "flags": ""},
        }
        adapter = StubSearchAdapter()
        matched = run_detection(_CHUNKS, config, adapter)
        assert len(matched) == len(_CHUNKS)

    def test_invalid_engine_raises(self):
        config = {"engine": "invalid_engine"}
        adapter = StubSearchAdapter()
        with pytest.raises(ValueError, match="Detection engine must be one of"):
            run_detection(_CHUNKS, config, adapter)

    def test_demo_mode_returns_first_n(self):
        config = {"engine": "regex", "regex": {"patterns": [], "flags": ""}}
        adapter = StubSearchAdapter(demo_mode=True, demo_n=2)
        matched = run_detection(_CHUNKS, config, adapter)
        assert len(matched) == 2
        assert all(mc.engine == "demo" for mc in matched)
        assert all(mc.score == pytest.approx(0.85) for mc in matched)

    def test_returns_matched_chunk_instances(self):
        config = {
            "engine": "regex",
            "regex": {"patterns": ["fee"], "flags": ""},
        }
        adapter = StubSearchAdapter()
        matched = run_detection(_CHUNKS, config, adapter)
        assert all(isinstance(mc, MatchedChunk) for mc in matched)
