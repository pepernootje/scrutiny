"""Detection page — configure and preview chunk detection.

Reads from session state: chunks.
Writes to session state: detection_config, matched_chunks.
"""

from __future__ import annotations

import logging

import streamlit as st

from scrutiny.app._sidebar import render_sidebar
from scrutiny.app.components.chunk_viewer import show_matched_chunks
from scrutiny.app.components.yaml_editor import yaml_editor
from scrutiny.config import make_search_adapter, resolve_config
from scrutiny.detection import run_detection

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Detection — Scrutiny", page_icon="🔎", layout="wide")

render_sidebar()

st.title("🔎 Detection")
st.markdown("Configure how chunks are filtered to find relevant passages.")

if not st.session_state.get("chunks"):
    st.warning("Please run the Chunking step first.")
    st.stop()

_DEFAULT_DETECTION_YAML = """\
engine: regex
regex:
  patterns:
    - "\\\\b(conflict|interest|commission|fee)\\\\b"
  flags: IGNORECASE
# azure_ai_search:
#   index_name: my-index
#   query: conflict of interest
#   top_k: 10
"""

_VALID_ENGINES = ["regex", "azure_ai_search", "hybrid"]

config = yaml_editor(
    label="Detection configuration",
    default_yaml=_DEFAULT_DETECTION_YAML,
    session_key="detection_config",
    download_filename="detection.yaml",
)

if config is not None:
    engine = config.get("engine", "")
    if engine not in _VALID_ENGINES:
        st.error(
            f"Detection engine must be one of: {', '.join(_VALID_ENGINES)}. "
            f"Got: {engine!r}"
        )
        config = None

if config is not None:
    st.session_state["detection_config"] = config

if st.button("▶ Run detection", type="primary"):
    if config is None:
        st.error("Fix the configuration errors above before running.")
    else:
        try:
            run_config = resolve_config()
            demo_mode: bool = st.session_state.get("demo_mode", False)
            adapter = make_search_adapter(run_config, demo_mode=demo_mode)
            chunks = st.session_state["chunks"]
            matched = run_detection(chunks, config, adapter)
            st.session_state["matched_chunks"] = matched
            st.success(f"Matched {len(matched)} / {len(chunks)} chunks.")
            logger.debug("Detection matched %d chunks", len(matched))
        except ValueError as exc:
            st.error(str(exc))
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception:
            logger.exception("Unexpected error during detection")
            st.error(
                "An unexpected error occurred during detection. "
                "Please check your configuration and try again."
            )

if st.session_state.get("matched_chunks") is not None:
    show_matched_chunks(st.session_state["matched_chunks"], title="Preview")
