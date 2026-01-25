"""Sidebar configuration component."""

import os
import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import API_BASE_URL


def render_sidebar():
    """Render the sidebar configuration panel."""
    st.header("Configuration")
    api_url = st.text_input("API URL", value=API_BASE_URL, key="api_url")
    if api_url != API_BASE_URL:
        st.session_state.api_url = api_url
        st.rerun()

    verbose = st.checkbox("Verbose Logging", value=False)

    st.divider()

