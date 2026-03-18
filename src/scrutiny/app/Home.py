"""Home page — document upload and check name selection.

Writes to session state: document, document_name, check_name.
"""

from __future__ import annotations

import logging

import streamlit as st

from scrutiny.app._sidebar import render_sidebar

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Scrutiny", page_icon="🔍", layout="wide")

render_sidebar()

st.title("🔍 Scrutiny Playground")
st.markdown(
    "Upload a prospectus PDF and enter a supervisory check name to get started."
)

st.header("1. Upload document")
uploaded_file = st.file_uploader(
    "Upload a PDF",
    type=["pdf"],
    help="Upload the prospectus PDF you want to analyse.",
)

if uploaded_file is not None:
    st.session_state["document"] = uploaded_file.read()
    st.session_state["document_name"] = uploaded_file.name
    st.success(f"Loaded: {uploaded_file.name}")
    logger.debug("Document uploaded: %s", uploaded_file.name)
elif st.session_state.get("document_name"):
    st.info(f"Using previously uploaded document: {st.session_state['document_name']}")

st.header("2. Enter check name")
check_name = st.text_input(
    "Supervisory check name",
    value=st.session_state.get("check_name", ""),
    placeholder="e.g. conflict_of_interest",
    help=(
        "Used as the folder name under configs/. "
        "Use lowercase letters, digits, and underscores."
    ),
)

if check_name:
    st.session_state["check_name"] = check_name.strip()

if st.session_state.get("document") and st.session_state.get("check_name"):
    st.success(
        "Ready! Use the sidebar to navigate to the Chunking page and start the pipeline."
    )
else:
    missing = []
    if not st.session_state.get("document"):
        missing.append("a PDF document")
    if not st.session_state.get("check_name"):
        missing.append("a check name")
    st.info(f"Please provide: {' and '.join(missing)}.")
