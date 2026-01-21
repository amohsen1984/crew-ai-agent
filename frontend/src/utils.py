"""Utility functions and session state initialization."""

import streamlit as st


def init_session_state():
    """Initialize Streamlit session state variables."""
    if "processing_status" not in st.session_state:
        st.session_state.processing_status = "idle"
    if "processing_job_id" not in st.session_state:
        st.session_state.processing_job_id = None
    if "processing_progress" not in st.session_state:
        st.session_state.processing_progress = 0
    if "processing_message" not in st.session_state:
        st.session_state.processing_message = ""
    if "edit_history" not in st.session_state:
        st.session_state.edit_history = []
    if "priority_rules" not in st.session_state:
        st.session_state.priority_rules = {
            "Bug": {"default": "Medium", "critical_keywords": ["data loss", "security", "crash"]},
            "Feature Request": {"default": "Low", "high_demand_keywords": ["urgent", "critical"]},
            "Complaint": {"default": "Medium", "high_keywords": ["subscription", "payment"]},
        }


def ensure_status_column(df: "pd.DataFrame") -> "pd.DataFrame":
    """Ensure status column exists in DataFrame, defaulting to 'pending'.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with status column.
    """
    import pandas as pd
    
    if "status" not in df.columns:
        df = df.copy()
        df["status"] = "pending"
    return df


