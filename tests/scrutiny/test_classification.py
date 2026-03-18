"""Tests for scrutiny.classification."""

import pytest

from scrutiny.adapters.stub_classification import StubClassificationAdapter
from scrutiny.classification import run_classification
from scrutiny.models import Chunk, ClassificationResult, MatchedChunk

_CONFIG = {
    "adapter": "azure_openai",
    "model": "gpt-4",
    "temperature": 0.0,
    "prompt_template": "Analyse this chunk: {{ chunk }}",
    "output_fields": ["decision", "justification"],
}

_CHUNKS = [
    Chunk(
        text="There may be conflicts of interest.",
        chunk_index=0,
        page_number=1,
        start_char=0,
        end_char=35,
    ),
    Chunk(
        text="Past performance is not a guarantee.",
        chunk_index=1,
        page_number=1,
        start_char=36,
        end_char=72,
    ),
]

_MATCHED = [
    MatchedChunk(chunk=_CHUNKS[0], score=1.0, engine="regex"),
    MatchedChunk(chunk=_CHUNKS[1], score=0.9, engine="regex"),
]


class TestRunClassification:
    def test_returns_results_for_all_chunks(self):
        adapter = StubClassificationAdapter()
        results = run_classification(_MATCHED, _CONFIG, adapter)
        assert len(results) == len(_MATCHED)
        assert all(isinstance(r, ClassificationResult) for r in results)

    def test_stub_results_have_is_stub_true(self):
        adapter = StubClassificationAdapter()
        results = run_classification(_MATCHED, _CONFIG, adapter)
        assert all(r.is_stub for r in results)

    def test_output_fields_contain_decision_and_justification(self):
        adapter = StubClassificationAdapter()
        results = run_classification(_MATCHED, _CONFIG, adapter)
        for r in results:
            assert "decision" in r.output_fields
            assert "justification" in r.output_fields

    def test_dev_mode_keyword_heuristic(self):
        adapter = StubClassificationAdapter(demo_mode=False)
        results = run_classification(_MATCHED, _CONFIG, adapter)
        # "conflict" is a keyword → YES
        assert results[0].output_fields["decision"] == "YES"
        assert "[Dev mode]" in results[0].output_fields["justification"]

    def test_demo_mode_first_chunk_yes(self):
        adapter = StubClassificationAdapter(demo_mode=True)
        results = run_classification(_MATCHED, _CONFIG, adapter)
        assert results[0].output_fields["decision"] == "YES"
        assert results[1].output_fields["decision"] == "NO"

    def test_invalid_adapter_raises(self):
        bad_config = dict(_CONFIG, adapter="unknown_adapter")
        adapter = StubClassificationAdapter()
        with pytest.raises(ValueError, match="Classification adapter must be one of"):
            run_classification(_MATCHED, bad_config, adapter)

    def test_missing_decision_field_raises(self):
        bad_config = dict(_CONFIG, output_fields=["justification"])
        adapter = StubClassificationAdapter()
        with pytest.raises(ValueError, match="output_fields must include"):
            run_classification(_MATCHED, bad_config, adapter)

    def test_missing_chunk_placeholder_raises(self):
        bad_config = dict(_CONFIG, prompt_template="No placeholder here")
        adapter = StubClassificationAdapter()
        with pytest.raises(ValueError, match="prompt_template must contain"):
            run_classification(_MATCHED, bad_config, adapter)

    def test_empty_matched_chunks(self):
        adapter = StubClassificationAdapter()
        results = run_classification([], _CONFIG, adapter)
        assert results == []
