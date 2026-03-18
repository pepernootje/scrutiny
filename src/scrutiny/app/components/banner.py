"""Reusable demo mode warning banner component."""

from __future__ import annotations

import streamlit as st


def show_demo_banner() -> None:
    """Display a yellow warning banner when demo mode is active.

    Only renders when ``st.session_state.demo_mode`` is ``True``.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    if st.session_state.get("demo_mode", False):
        st.warning(
            "🧪 Demo mode active — results are simulated and do not reflect "
            "real detection behaviour."
        )
