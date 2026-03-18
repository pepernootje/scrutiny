"""Shared sidebar renderer used on every page."""

from __future__ import annotations

import streamlit as st

from scrutiny.app.components.banner import show_demo_banner


def render_sidebar() -> None:
    """Render the persistent sidebar on every page.

    Shows the current document name, check name, and demo mode toggle.
    Also shows the demo mode banner when active.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    with st.sidebar:
        st.header("Scrutiny")

        doc_name = st.session_state.get("document_name") or "No document loaded"
        check_name = st.session_state.get("check_name") or "No check selected"

        st.markdown(f"**Document:** {doc_name}")
        st.markdown(f"**Check:** {check_name}")

        st.divider()

        demo_mode = st.toggle(
            "🧪 Demo mode",
            value=st.session_state.get("demo_mode", False),
            help="Simulate results without running real detection or classification.",
        )
        st.session_state["demo_mode"] = demo_mode

    show_demo_banner()
