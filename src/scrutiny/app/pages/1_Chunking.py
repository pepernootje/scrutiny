"""Chunking page — configure and preview document chunking.

Reads from session state: document.
Writes to session state: chunking_config, chunks.
"""

from __future__ import annotations

import logging

import pdfplumber
import streamlit as st

from scrutiny.app._sidebar import render_sidebar
from scrutiny.app.components.chunk_viewer import show_chunks
from scrutiny.app.components.yaml_editor import yaml_editor
from scrutiny.chunking import chunk_document

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Chunking — Scrutiny", page_icon="✂️", layout="wide")

render_sidebar()

st.title("✂️ Chunking")
st.markdown("Configure how the document is split into candidate chunks.")

if not st.session_state.get("document"):
    st.warning("Please upload a document on the Home page first.")
    st.stop()

_DEFAULT_CHUNKING_YAML = """\
method: paragraph
chunk_size: 500
overlap: 0
# boundary_pattern is only used when method is regex_boundary
# boundary_pattern: "\\n{2,}"
"""

_VALID_METHODS = ["sentence", "paragraph", "token_window", "regex_boundary"]

config = yaml_editor(
    label="Chunking configuration",
    default_yaml=_DEFAULT_CHUNKING_YAML,
    session_key="chunking_config",
    download_filename="chunking.yaml",
)

if config is not None:
    method = config.get("method", "")
    if method not in _VALID_METHODS:
        st.error(
            f"Chunking method must be one of: {', '.join(_VALID_METHODS)}. "
            f"Got: {method!r}"
        )
        config = None

if config is not None:
    st.session_state["chunking_config"] = config

if st.button("▶ Run chunking", type="primary"):
    if config is None:
        st.error("Fix the configuration errors above before running.")
    else:
        try:
            pdf_bytes: bytes = st.session_state["document"]
            text_parts: list[str] = []
            with pdfplumber.open(pdf_bytes) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    if page_text:
                        text_parts.append(page_text)
            full_text = "\n\n".join(text_parts)

            if not full_text.strip():
                st.error(
                    "Could not extract any text from the PDF. "
                    "The file may be scanned or image-only."
                )
            else:
                chunks = chunk_document(full_text, config)
                st.session_state["chunks"] = chunks
                st.success(f"Produced {len(chunks)} chunks.")
                logger.debug("Chunking produced %d chunks", len(chunks))
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            logger.exception("Unexpected error during chunking")
            st.error(
                "An unexpected error occurred during chunking. "
                "Please check your configuration and try again."
            )

if st.session_state.get("chunks"):
    show_chunks(st.session_state["chunks"], title="Preview")
