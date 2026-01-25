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
            "Bug": {
                "default": "Medium",
                "critical_keywords": ["crash", "data loss", "complete data loss", "all data", "unusable", "cannot access", "app won't start", "startup crash"],
                "high_keywords": ["blank screen", "freeze", "notifications not working", "not responding", "slow", "performance", "lag", "frozen", "stuck"],
                "medium_keywords": ["permission", "security", "unexpected", "question", "concern", "explanation"],
                "low_keywords": ["cosmetic", "minor", "typo", "spelling", "text"],
            },
            "Feature Request": {
                "default": "Low",
                "critical_keywords": [],
                "high_keywords": [],
                "medium_keywords": ["widget", "integration", "calendar", "recurring", "offline", "sync", "collaboration", "team"],
                "low_keywords": ["dark mode", "theme", "color", "shortcut", "voice", "Siri", "simple"],
            },
            "Complaint": {
                "default": "Medium",
                "critical_keywords": [],
                "high_keywords": ["billing", "payment", "charge", "refund", "duplicate charge", "subscription", "premium", "paid"],
                "medium_keywords": ["support", "response time", "customer service", "performance", "UI", "design", "slow"],
                "low_keywords": ["suggestion", "preference", "minor"],
            },
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


