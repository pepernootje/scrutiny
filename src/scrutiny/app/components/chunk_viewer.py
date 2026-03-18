"""Reusable chunk viewer component.

Renders a list of Chunk or MatchedChunk objects as a Streamlit table.
"""

from __future__ import annotations

import streamlit as st

from scrutiny.models import Chunk, MatchedChunk


def show_chunks(chunks: list[Chunk], title: str = "Chunks") -> None:
    """Render a list of Chunk objects as a table.

    Parameters
    ----------
    chunks : list of Chunk
        Chunks to display.
    title : str
        Section header shown above the table.

    Returns
    -------
    None
    """
    st.subheader(title)
    if not chunks:
        st.info("No chunks to display.")
        return

    rows = [
        {
            "Index": c.chunk_index,
            "Page": c.page_number if c.page_number is not None else "—",
            "Start": c.start_char,
            "End": c.end_char,
            "Text (preview)": c.text[:120] + "…" if len(c.text) > 120 else c.text,
        }
        for c in chunks
    ]
    st.dataframe(rows, use_container_width=True)


def show_matched_chunks(
    matched_chunks: list[MatchedChunk], title: str = "Matched Chunks"
) -> None:
    """Render a list of MatchedChunk objects as a table.

    Parameters
    ----------
    matched_chunks : list of MatchedChunk
        Matched chunks to display.
    title : str
        Section header shown above the table.

    Returns
    -------
    None
    """
    st.subheader(title)
    if not matched_chunks:
        st.info("No matched chunks to display.")
        return

    rows = [
        {
            "Index": mc.chunk.chunk_index,
            "Page": mc.chunk.page_number if mc.chunk.page_number is not None else "—",
            "Score": f"{mc.score:.2f}",
            "Engine": mc.engine,
            "Text (preview)": (
                mc.chunk.text[:120] + "…"
                if len(mc.chunk.text) > 120
                else mc.chunk.text
            ),
        }
        for mc in matched_chunks
    ]
    st.dataframe(rows, use_container_width=True)
