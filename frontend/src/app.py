"""Streamlit UI for feedback processing dashboard."""

import warnings
from dotenv import load_dotenv

import streamlit as st

from api_client import api_request, API_BASE_URL
from utils import init_session_state
from components import (
    sidebar as sidebar_component,
    processing_status as processing_status_component,
    dashboard as dashboard_component,
    tickets as tickets_component,
    manual_override as manual_override_component,
    configuration as configuration_component,
    analytics as analytics_component,
)

# Suppress warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*signal.*")

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Feedback Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
init_session_state()


def main():
    """Main Streamlit app."""
    st.title("📊 Feedback Analysis Dashboard")

    # Check API connection
    health = api_request("GET", "/api/v1/health")
    if not health:
        st.error(
            f"⚠️ Cannot connect to backend API at {API_BASE_URL}. "
            "Please ensure the backend is running."
        )
        st.stop()

    # Sidebar configuration
    with st.sidebar:
        sidebar_component.render_sidebar()
        processing_status_component.render_processing_status()

    # Main content area
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Dashboard", "Tickets", "Manual Override", "Configuration", "Analytics"]
    )

    with tab1:
        dashboard_component.render_dashboard()

    with tab2:
        tickets_component.render_tickets()

    with tab3:
        manual_override_component.render_manual_override()

    with tab4:
        configuration_component.render_configuration()

    with tab5:
        analytics_component.render_analytics()


if __name__ == "__main__":
    main()
