"""Classification page — configure and preview LLM classification.

Reads from session state: matched_chunks.
Writes to session state: classification_config, results.
"""

from __future__ import annotations

import logging

import streamlit as st

from scrutiny.app._sidebar import render_sidebar
from scrutiny.app.components.yaml_editor import yaml_editor
from scrutiny.classification import run_classification
from scrutiny.config import make_classification_adapter, resolve_config

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Classification — Scrutiny", page_icon="🧠", layout="wide"
)

render_sidebar()

st.title("🧠 Classification")
st.markdown("Configure the LLM prompt and preview classification results.")

if not st.session_state.get("matched_chunks"):
    st.warning("Please run the Detection step first.")
    st.stop()

_DEFAULT_CLASSIFICATION_YAML = """\
adapter: azure_openai
model: gpt-4
temperature: 0.0
prompt_template: |
  You are a compliance analyst reviewing a prospectus document.
  Topic: {{ topic }}

  Chunk:
  {{ chunk }}

  Respond with:
  DECISION: YES or NO
  JUSTIFICATION: one sentence explaining your decision
output_fields:
  - decision
  - justification
"""

config = yaml_editor(
    label="Classification configuration",
    default_yaml=_DEFAULT_CLASSIFICATION_YAML,
    session_key="classification_config",
    download_filename="classification.yaml",
)

if config is not None:
    errors: list[str] = []
    adapter_val = config.get("adapter", "")
    if adapter_val not in {"azure_openai"}:
        errors.append(
            f"Classification adapter must be 'azure_openai'. Got: {adapter_val!r}"
        )
    output_fields = config.get("output_fields", [])
    for required in ("decision", "justification"):
        if required not in output_fields:
            errors.append(f"output_fields must include '{required}'")
    if "{{ chunk }}" not in config.get("prompt_template", ""):
        errors.append("prompt_template must contain the placeholder {{ chunk }}")
    for err in errors:
        st.error(err)
    if errors:
        config = None

if config is not None:
    st.session_state["classification_config"] = config

if st.button("▶ Run classification", type="primary"):
    if config is None:
        st.error("Fix the configuration errors above before running.")
    else:
        try:
            run_config = resolve_config()
            demo_mode: bool = st.session_state.get("demo_mode", False)
            adapter = make_classification_adapter(run_config, demo_mode=demo_mode)
            matched = st.session_state["matched_chunks"]
            results = run_classification(matched, config, adapter)
            st.session_state["results"] = results
            yes_count = sum(
                1
                for r in results
                if r.output_fields.get("decision", "").upper() == "YES"
            )
            st.success(
                f"Classified {len(results)} chunks. "
                f"{yes_count} YES / {len(results) - yes_count} NO."
            )
            logger.debug("Classification produced %d results", len(results))
        except ValueError as exc:
            st.error(str(exc))
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception:
            logger.exception("Unexpected error during classification")
            st.error(
                "An unexpected error occurred during classification. "
                "Please check your configuration and try again."
            )

if st.session_state.get("results"):
    st.subheader("Preview")
    results = st.session_state["results"]
    rows = [
        {
            "Index": r.matched_chunk.chunk.chunk_index,
            "Decision": r.output_fields.get("decision", ""),
            "Justification": r.output_fields.get("justification", ""),
            "Model": r.model,
            "Stub": "✓" if r.is_stub else "✗",
            "Text (preview)": (
                r.matched_chunk.chunk.text[:100] + "…"
                if len(r.matched_chunk.chunk.text) > 100
                else r.matched_chunk.chunk.text
            ),
        }
        for r in results
    ]
    st.dataframe(rows, use_container_width=True)
