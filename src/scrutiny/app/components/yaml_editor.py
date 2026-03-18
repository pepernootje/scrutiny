"""Reusable YAML editor component.

Combines a text_area, file_uploader, and download_button into a single
component for editing YAML configuration files.
"""

from __future__ import annotations

import logging

import streamlit as st
import yaml

logger = logging.getLogger(__name__)


def yaml_editor(
    label: str,
    default_yaml: str,
    session_key: str,
    file_uploader_key: str | None = None,
    download_filename: str = "config.yaml",
) -> dict | None:
    """Render a YAML editor with upload and download controls.

    The editor is pre-populated with ``default_yaml`` when the session key
    holds no value.  Uploaded files replace the editor content.  Returns
    the parsed YAML dict, or ``None`` if parsing fails.

    Parameters
    ----------
    label : str
        Label shown above the text area.
    default_yaml : str
        Default YAML content shown when the editor is empty.
    session_key : str
        Session state key for the parsed config dict.
    file_uploader_key : str or None
        Optional unique key for the file uploader widget.
    download_filename : str
        Filename used for the download button.

    Returns
    -------
    dict or None
        Parsed YAML configuration, or ``None`` on parse error.
    """
    uploader_key = file_uploader_key or f"_upload_{session_key}"

    uploaded = st.file_uploader(
        f"Upload {label} (.yaml/.yml)",
        type=["yaml", "yml"],
        key=uploader_key,
    )

    if uploaded is not None:
        try:
            raw = uploaded.read().decode("utf-8")
        except Exception:
            st.error("Could not read the uploaded file. Please try again.")
            raw = default_yaml
    else:
        existing = st.session_state.get(session_key)
        raw = yaml.dump(existing, default_flow_style=False) if existing else default_yaml

    edited = st.text_area(label, value=raw, height=300, key=f"_text_{session_key}")

    parsed: dict | None = None
    try:
        parsed = yaml.safe_load(edited)
        if not isinstance(parsed, dict):
            st.error("YAML must be a mapping (key: value pairs) at the top level.")
            parsed = None
    except yaml.YAMLError as exc:
        st.error(f"Invalid YAML: {exc}")

    col1, _ = st.columns([1, 3])
    with col1:
        st.download_button(
            label=f"Download {download_filename}",
            data=edited,
            file_name=download_filename,
            mime="text/yaml",
        )

    return parsed
