"""Results page — view full output, download YAML, compare runs.

Reads from session state: chunks, matched_chunks, results,
    chunking_config, detection_config, classification_config.
Writes to session state: run_history.
"""

from __future__ import annotations

import logging
from datetime import datetime

import streamlit as st
import yaml

from scrutiny.app._sidebar import render_sidebar

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Results — Scrutiny", page_icon="📊", layout="wide")

render_sidebar()

st.title("📊 Results")
st.markdown("Review the full pipeline output, download YAML, and compare runs.")

results = st.session_state.get("results")
if not results:
    st.warning("Please run the Classification step first.")
    st.stop()

chunks = st.session_state.get("chunks", [])
matched_chunks = st.session_state.get("matched_chunks", [])
chunking_config = st.session_state.get("chunking_config", {})
detection_config = st.session_state.get("detection_config", {})
classification_config = st.session_state.get("classification_config", {})
document_name = st.session_state.get("document_name", "")
check_name = st.session_state.get("check_name", "")
demo_mode: bool = st.session_state.get("demo_mode", False)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
yes_count = sum(
    1 for r in results if r.output_fields.get("decision", "").upper() == "YES"
)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total chunks", len(chunks))
col2.metric("Matched chunks", len(matched_chunks))
col3.metric("YES", yes_count)
col4.metric("NO", len(results) - yes_count)

# ---------------------------------------------------------------------------
# Full results table
# ---------------------------------------------------------------------------
st.subheader("Full results")
result_rows = []
for r in results:
    row = {
        "Index": r.matched_chunk.chunk.chunk_index,
        "Page": (
            r.matched_chunk.chunk.page_number
            if r.matched_chunk.chunk.page_number is not None
            else "—"
        ),
        "Score": f"{r.matched_chunk.score:.2f}",
        "Engine": r.matched_chunk.engine,
        "Decision": r.output_fields.get("decision", ""),
        "Justification": r.output_fields.get("justification", ""),
        "Stub": "✓" if r.is_stub else "✗",
        "Text": r.matched_chunk.chunk.text,
    }
    # Add any extra output fields
    for k, v in r.output_fields.items():
        if k not in {"decision", "justification"}:
            row[k] = v
    result_rows.append(row)

st.dataframe(result_rows, use_container_width=True)

# ---------------------------------------------------------------------------
# YAML output generation
# ---------------------------------------------------------------------------
timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
mode = "demo" if demo_mode else ("production" if False else "development")

output_doc = {
    "run": {
        "timestamp": timestamp,
        "document_name": document_name,
        "check_name": check_name,
        "mode": mode,
    },
    "config": {
        "chunking": chunking_config,
        "detection": detection_config,
        "classification": classification_config,
    },
    "results": [
        {
            "chunk_index": r.matched_chunk.chunk.chunk_index,
            "page_number": r.matched_chunk.chunk.page_number,
            "text": r.matched_chunk.chunk.text,
            "score": r.matched_chunk.score,
            "engine": r.matched_chunk.engine,
            "decision": r.output_fields.get("decision", ""),
            "justification": r.output_fields.get("justification", ""),
            "is_stub": r.is_stub,
        }
        for r in results
    ],
}

output_yaml = yaml.dump(output_doc, default_flow_style=False, allow_unicode=True)
output_filename = f"output_{timestamp}.yaml"

st.download_button(
    label=f"⬇ Download {output_filename}",
    data=output_yaml,
    file_name=output_filename,
    mime="text/yaml",
)

# ---------------------------------------------------------------------------
# Configs viewer
# ---------------------------------------------------------------------------
st.subheader("Configurations")
col_c, col_d, col_e = st.columns(3)
with col_c:
    st.markdown("**Chunking**")
    chunking_yaml = yaml.dump(chunking_config, default_flow_style=False, allow_unicode=True)
    st.code(chunking_yaml, language="yaml")
    st.download_button(
        "⬇ chunking.yaml",
        data=chunking_yaml,
        file_name="chunking.yaml",
        mime="text/yaml",
        key="dl_chunking",
    )
with col_d:
    st.markdown("**Detection**")
    detection_yaml = yaml.dump(detection_config, default_flow_style=False, allow_unicode=True)
    st.code(detection_yaml, language="yaml")
    st.download_button(
        "⬇ detection.yaml",
        data=detection_yaml,
        file_name="detection.yaml",
        mime="text/yaml",
        key="dl_detection",
    )
with col_e:
    st.markdown("**Classification**")
    classification_yaml = yaml.dump(
        classification_config, default_flow_style=False, allow_unicode=True
    )
    st.code(classification_yaml, language="yaml")
    st.download_button(
        "⬇ classification.yaml",
        data=classification_yaml,
        file_name="classification.yaml",
        mime="text/yaml",
        key="dl_classification",
    )

# ---------------------------------------------------------------------------
# Save to run history
# ---------------------------------------------------------------------------
if st.button("💾 Save to run history"):
    history: list[dict] = st.session_state.get("run_history", [])
    history.append(output_doc)
    st.session_state["run_history"] = history
    st.success(f"Run saved. History contains {len(history)} run(s).")
    logger.debug("Saved run to history; total runs: %d", len(history))

# ---------------------------------------------------------------------------
# Run comparison
# ---------------------------------------------------------------------------
run_history: list[dict] = st.session_state.get("run_history", [])
if len(run_history) >= 2:
    st.subheader("Run comparison")
    run_labels = [
        f"Run {i + 1} — {r['run']['timestamp']}" for i, r in enumerate(run_history)
    ]
    col_a, col_b = st.columns(2)
    with col_a:
        idx_a = st.selectbox("Run A", range(len(run_history)), format_func=lambda i: run_labels[i])
    with col_b:
        idx_b = st.selectbox(
            "Run B",
            range(len(run_history)),
            index=min(1, len(run_history) - 1),
            format_func=lambda i: run_labels[i],
        )

    run_a = run_history[idx_a]
    run_b = run_history[idx_b]

    st.markdown("**Run A results**")
    st.dataframe(run_a["results"], use_container_width=True)
    st.markdown("**Run B results**")
    st.dataframe(run_b["results"], use_container_width=True)
