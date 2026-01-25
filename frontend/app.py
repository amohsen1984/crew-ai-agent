"""Streamlit UI for feedback processing dashboard."""

import json
import logging
import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

# Suppress warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*signal.*")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Feedback Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "processing_status" not in st.session_state:
    st.session_state.processing_status = "idle"
if "edit_history" not in st.session_state:
    st.session_state.edit_history = []
if "priority_rules" not in st.session_state:
    st.session_state.priority_rules = {
        "Bug": {"default": "Medium", "critical_keywords": ["data loss", "security", "crash"]},
        "Feature Request": {"default": "Low", "high_demand_keywords": ["urgent", "critical"]},
        "Complaint": {"default": "Medium", "high_keywords": ["subscription", "payment"]},
    }


def api_request(method: str, endpoint: str, **kwargs) -> Optional[Dict]:
    """Make API request to backend.

    Args:
        method: HTTP method (GET, POST, PATCH).
        endpoint: API endpoint path.
        **kwargs: Additional arguments for requests.

    Returns:
        Response JSON or None on error.
    """
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs, timeout=300)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        st.error(f"API Error: {str(e)}")
        return None


def load_tickets() -> pd.DataFrame:
    """Load generated tickets from API.

    Returns:
        DataFrame with tickets or empty DataFrame.
    """
    response = api_request("GET", "/api/v1/tickets", params={"limit": 1000})
    if response:
        return pd.DataFrame(response)
    return pd.DataFrame()


def load_metrics() -> pd.DataFrame:
    """Load metrics from API.

    Returns:
        DataFrame with metrics or empty DataFrame.
    """
    response = api_request("GET", "/api/v1/metrics")
    if response and "metrics" in response:
        return pd.DataFrame(response["metrics"])
    return pd.DataFrame()


def load_stats() -> Dict:
    """Load summary statistics from API.

    Returns:
        Dictionary with statistics.
    """
    response = api_request("GET", "/api/v1/stats")
    return response or {}


def process_feedback() -> Dict:
    """Process feedback via API.

    Returns:
        Processing result dictionary.
    """
    response = api_request("POST", "/api/v1/process")
    return response or {"status": "error", "error": "API request failed"}


def update_ticket(ticket_id: str, updates: Dict) -> Dict:
    """Update a ticket via API.

    Args:
        ticket_id: Ticket ID to update.
        updates: Dictionary of fields to update.

    Returns:
        Update result dictionary.
    """
    response = api_request("PATCH", f"/api/v1/tickets/{ticket_id}", json=updates)
    return response or {"status": "error", "error": "API request failed"}


def save_ticket_edit(
    ticket_id: str,
    action: str,
    changes: Dict,
    output_dir: str = "output",
) -> None:
    """Save ticket edit to history.

    Args:
        ticket_id: Ticket ID being edited.
        action: Action taken (approve/reject/edit).
        changes: Dictionary of changes made.
        output_dir: Output directory path.
    """
    edit_entry = {
        "timestamp": datetime.now().isoformat(),
        "ticket_id": ticket_id,
        "action": action,
        "changes": json.dumps(changes),
    }
    st.session_state.edit_history.append(edit_entry)

    # Save to file
    history_file = Path(output_dir) / "edit_history.json"
    history_data = st.session_state.edit_history
    with open(history_file, "w") as f:
        json.dump(history_data, f, indent=2)


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
        st.header("Configuration")
        api_url = st.text_input("API URL", value=API_BASE_URL, key="api_url")
        if api_url != API_BASE_URL:
            st.session_state.api_url = api_url
            st.rerun()

        verbose = st.checkbox("Verbose Logging", value=False)
        classification_threshold = st.slider(
            "Classification Threshold", 0.5, 0.9, 0.7, 0.05
        )

        st.divider()

        # Processing status indicator
        st.subheader("Processing Status")
        status_emoji = {
            "idle": "⚪",
            "processing": "🟡",
            "completed": "🟢",
            "error": "🔴",
        }
        status = st.session_state.processing_status
        st.write(f"{status_emoji.get(status, '⚪')} {status.capitalize()}")

        if st.button("🚀 Process Feedback", type="primary"):
            st.session_state.processing_status = "processing"
            with st.spinner("Processing feedback..."):
                result = process_feedback()
                if result.get("status") == "success":
                    st.session_state.processing_status = "completed"
                    data = result.get("data", {})
                    st.success(
                        f"Processed {data.get('processed', 0)} items. "
                        f"Generated {data.get('tickets', 0)} tickets."
                    )
                else:
                    st.session_state.processing_status = "error"
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
                st.rerun()

    # Main content area
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Dashboard", "Tickets", "Manual Override", "Configuration", "Analytics"]
    )

    with tab1:
        st.header("Dashboard Overview")

        # Load data
        tickets_df = load_tickets()
        stats = load_stats()

        if tickets_df.empty:
            st.info("No tickets generated yet. Click 'Process Feedback' to start.")
        else:
            # Summary cards
            st.subheader("Summary")
            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:
                st.metric("Total Tickets", stats.get("total_tickets", len(tickets_df)))

            with col2:
                bugs = stats.get("by_category", {}).get("Bug", 0)
                st.metric("Bugs", bugs)

            with col3:
                features = stats.get("by_category", {}).get("Feature Request", 0)
                st.metric("Features", features)

            with col4:
                critical = stats.get("by_priority", {}).get("Critical", 0)
                st.metric("Critical", critical)

            with col5:
                high = stats.get("by_priority", {}).get("High", 0)
                st.metric("High Priority", high)

            with col6:
                avg_conf = stats.get("avg_confidence", 0.0)
                st.metric("Avg Confidence", f"{avg_conf:.2%}")

            st.divider()

            # Quick filters
            st.subheader("Quick Filters")
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                quick_category = st.selectbox(
                    "Filter by Category",
                    ["All"] + list(tickets_df["category"].unique()) if not tickets_df.empty else [],
                    key="dashboard_category_filter",
                )
            with filter_col2:
                quick_priority = st.selectbox(
                    "Filter by Priority",
                    ["All"] + list(tickets_df["priority"].unique()) if not tickets_df.empty else [],
                    key="dashboard_priority_filter",
                )

            # Apply filters
            filtered_dashboard_df = tickets_df.copy()
            if quick_category != "All" and not tickets_df.empty:
                filtered_dashboard_df = filtered_dashboard_df[
                    filtered_dashboard_df["category"] == quick_category
                ]
            if quick_priority != "All" and not tickets_df.empty:
                filtered_dashboard_df = filtered_dashboard_df[
                    filtered_dashboard_df["priority"] == quick_priority
                ]

            # Recent tickets table
            st.subheader("Recent Tickets")
            if not filtered_dashboard_df.empty:
                display_df = filtered_dashboard_df.head(20)[
                    ["ticket_id", "title", "category", "priority", "confidence"]
                ]
                st.dataframe(display_df, use_container_width=True)

                # Category distribution
                st.subheader("Category Distribution")
                category_counts = filtered_dashboard_df["category"].value_counts()
                st.bar_chart(category_counts)

    with tab2:
        st.header("Generated Tickets")

        tickets_df = load_tickets()

        if tickets_df.empty:
            st.info("No tickets available.")
        else:
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                category_filter = st.selectbox(
                    "Filter by Category",
                    ["All"] + list(tickets_df["category"].unique()),
                )
            with col2:
                priority_filter = st.selectbox(
                    "Filter by Priority",
                    ["All"] + list(tickets_df["priority"].unique()),
                )

            # Apply filters
            filtered_df = tickets_df.copy()
            if category_filter != "All":
                filtered_df = filtered_df[
                    filtered_df["category"] == category_filter
                ]
            if priority_filter != "All":
                filtered_df = filtered_df[
                    filtered_df["priority"] == priority_filter
                ]

            st.dataframe(filtered_df, use_container_width=True)

    with tab3:
        st.header("Manual Override")

        tickets_df = load_tickets()

        if tickets_df.empty:
            st.info("No tickets available for editing.")
        else:
            # Ticket selection
            ticket_options = [
                f"{row['ticket_id']} - {row['title'][:50]}"
                for _, row in tickets_df.iterrows()
            ]
            selected_ticket_str = st.selectbox(
                "Select Ticket to Edit", ticket_options
            )

            if selected_ticket_str:
                selected_ticket_id = selected_ticket_str.split(" - ")[0]
                selected_ticket = tickets_df[
                    tickets_df["ticket_id"] == selected_ticket_id
                ].iloc[0]

                st.divider()

                # Ticket editor form
                with st.form("ticket_editor_form"):
                    st.subheader("Edit Ticket")

                    col1, col2 = st.columns(2)

                    with col1:
                        edited_title = st.text_input(
                            "Title", value=selected_ticket["title"]
                        )
                        edited_category = st.selectbox(
                            "Category",
                            ["Bug", "Feature Request", "Praise", "Complaint", "Spam"],
                            index=[
                                "Bug",
                                "Feature Request",
                                "Praise",
                                "Complaint",
                                "Spam",
                            ].index(selected_ticket["category"]),
                        )
                        edited_priority = st.selectbox(
                            "Priority",
                            ["Critical", "High", "Medium", "Low"],
                            index=["Critical", "High", "Medium", "Low"].index(
                                selected_ticket["priority"]
                            ),
                        )

                    with col2:
                        edited_description = st.text_area(
                            "Description",
                            value=selected_ticket.get("description", ""),
                            height=150,
                        )
                        edited_technical_details = st.text_area(
                            "Technical Details",
                            value=selected_ticket.get("technical_details", ""),
                            height=100,
                        )

                    col_btn1, col_btn2, col_btn3 = st.columns(3)

                    with col_btn1:
                        approve_btn = st.form_submit_button("✅ Approve", type="primary")
                    with col_btn2:
                        reject_btn = st.form_submit_button("❌ Reject")
                    with col_btn3:
                        save_btn = st.form_submit_button("💾 Save Changes")

                    if approve_btn:
                        changes = {
                            "title": edited_title,
                            "category": edited_category,
                            "priority": edited_priority,
                        }
                        result = update_ticket(selected_ticket_id, changes)
                        if result.get("status") == "success":
                            save_ticket_edit(
                                selected_ticket_id, "approve", changes, "output"
                            )
                            st.success(f"Ticket {selected_ticket_id} approved!")
                        else:
                            st.error(f"Error: {result.get('error', 'Unknown error')}")

                    if reject_btn:
                        changes = {"status": "rejected"}
                        save_ticket_edit(
                            selected_ticket_id, "reject", changes, "output"
                        )
                        st.warning(f"Ticket {selected_ticket_id} rejected!")

                    if save_btn:
                        changes = {
                            "title": edited_title,
                            "category": edited_category,
                            "priority": edited_priority,
                            "description": edited_description,
                            "technical_details": edited_technical_details,
                        }
                        result = update_ticket(selected_ticket_id, changes)
                        if result.get("status") == "success":
                            save_ticket_edit(
                                selected_ticket_id, "edit", changes, "output"
                            )
                            st.success(f"Changes saved for ticket {selected_ticket_id}!")
                        else:
                            st.error(f"Error: {result.get('error', 'Unknown error')}")

            st.divider()

            # Batch approval
            st.subheader("Batch Approval")
            st.write("Select multiple tickets with similar characteristics:")

            if not tickets_df.empty:
                batch_category = st.selectbox(
                    "Category for Batch",
                    ["All"] + list(tickets_df["category"].unique()),
                    key="batch_category",
                )
                batch_priority = st.selectbox(
                    "Priority for Batch",
                    ["All"] + list(tickets_df["priority"].unique()),
                    key="batch_priority",
                )

                if batch_category != "All" or batch_priority != "All":
                    batch_tickets = tickets_df.copy()
                    if batch_category != "All":
                        batch_tickets = batch_tickets[
                            batch_tickets["category"] == batch_category
                        ]
                    if batch_priority != "All":
                        batch_tickets = batch_tickets[
                            batch_tickets["priority"] == batch_priority
                        ]

                    st.write(f"Found {len(batch_tickets)} tickets matching criteria")

                    if st.button("✅ Approve All Matching", type="primary"):
                        approved_count = 0
                        for _, ticket in batch_tickets.iterrows():
                            changes = {
                                "category": batch_category if batch_category != "All" else ticket["category"],
                                "priority": batch_priority if batch_priority != "All" else ticket["priority"],
                            }
                            result = update_ticket(ticket["ticket_id"], changes)
                            if result.get("status") == "success":
                                approved_count += 1
                        st.success(f"Approved {approved_count} tickets!")

            st.divider()

            # Edit history log
            st.subheader("Edit History")
            if st.session_state.edit_history:
                history_df = pd.DataFrame(st.session_state.edit_history)
                st.dataframe(history_df, use_container_width=True)
            else:
                st.info("No edit history yet.")

    with tab4:
        st.header("Configuration Panel")

        st.subheader("Processing Settings")
        st.text_input("LLM Model", value=os.getenv("MODEL_NAME", "gpt-4"), disabled=True)
        st.slider("Classification Threshold", 0.5, 0.9, 0.7, 0.05, disabled=True)

        st.divider()

        st.subheader("Priority Override Rules")
        # Same as before - these are frontend-only settings
        with st.expander("Bug Priority Rules"):
            bug_default = st.selectbox(
                "Default Priority",
                ["Critical", "High", "Medium", "Low"],
                index=["Critical", "High", "Medium", "Low"].index(
                    st.session_state.priority_rules["Bug"]["default"]
                ),
                key="bug_default",
            )
            bug_critical_keywords = st.text_input(
                "Critical Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Bug"].get("critical_keywords", [])
                ),
                key="bug_critical_keywords",
            )
            bug_high_keywords = st.text_input(
                "High Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Bug"].get("high_keywords", [])
                ),
                key="bug_high_keywords",
            )
            bug_medium_keywords = st.text_input(
                "Medium Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Bug"].get("medium_keywords", [])
                ),
                key="bug_medium_keywords",
            )
            bug_low_keywords = st.text_input(
                "Low Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Bug"].get("low_keywords", [])
                ),
                key="bug_low_keywords",
            )
            if st.button("Save Bug Rules", key="save_bug"):
                st.session_state.priority_rules["Bug"] = {
                    "default": bug_default,
                    "critical_keywords": [k.strip() for k in bug_critical_keywords.split(",") if k.strip()],
                    "high_keywords": [k.strip() for k in bug_high_keywords.split(",") if k.strip()],
                    "medium_keywords": [k.strip() for k in bug_medium_keywords.split(",") if k.strip()],
                    "low_keywords": [k.strip() for k in bug_low_keywords.split(",") if k.strip()],
                }
                st.success("Bug priority rules saved!")

        with st.expander("Feature Request Priority Rules"):
            feature_default = st.selectbox(
                "Default Priority",
                ["Critical", "High", "Medium", "Low"],
                index=["Critical", "High", "Medium", "Low"].index(
                    st.session_state.priority_rules["Feature Request"]["default"]
                ),
                key="feature_default",
            )
            feature_critical_keywords = st.text_input(
                "Critical Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Feature Request"].get("critical_keywords", [])
                ),
                key="feature_critical_keywords",
            )
            feature_high_keywords = st.text_input(
                "High Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Feature Request"].get("high_keywords", [])
                ),
                key="feature_high_keywords",
            )
            feature_medium_keywords = st.text_input(
                "Medium Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Feature Request"].get("medium_keywords", [])
                ),
                key="feature_medium_keywords",
            )
            feature_low_keywords = st.text_input(
                "Low Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Feature Request"].get("low_keywords", [])
                ),
                key="feature_low_keywords",
            )
            if st.button("Save Feature Rules", key="save_feature"):
                st.session_state.priority_rules["Feature Request"] = {
                    "default": feature_default,
                    "critical_keywords": [k.strip() for k in feature_critical_keywords.split(",") if k.strip()],
                    "high_keywords": [k.strip() for k in feature_high_keywords.split(",") if k.strip()],
                    "medium_keywords": [k.strip() for k in feature_medium_keywords.split(",") if k.strip()],
                    "low_keywords": [k.strip() for k in feature_low_keywords.split(",") if k.strip()],
                }
                st.success("Feature Request priority rules saved!")

        with st.expander("Complaint Priority Rules"):
            complaint_default = st.selectbox(
                "Default Priority",
                ["Critical", "High", "Medium", "Low"],
                index=["Critical", "High", "Medium", "Low"].index(
                    st.session_state.priority_rules["Complaint"]["default"]
                ),
                key="complaint_default",
            )
            complaint_critical_keywords = st.text_input(
                "Critical Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Complaint"].get("critical_keywords", [])
                ),
                key="complaint_critical_keywords",
            )
            complaint_high_keywords = st.text_input(
                "High Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Complaint"].get("high_keywords", [])
                ),
                key="complaint_high_keywords",
            )
            complaint_medium_keywords = st.text_input(
                "Medium Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Complaint"].get("medium_keywords", [])
                ),
                key="complaint_medium_keywords",
            )
            complaint_low_keywords = st.text_input(
                "Low Keywords (comma-separated)",
                value=", ".join(
                    st.session_state.priority_rules["Complaint"].get("low_keywords", [])
                ),
                key="complaint_low_keywords",
            )
            if st.button("Save Complaint Rules", key="save_complaint"):
                st.session_state.priority_rules["Complaint"] = {
                    "default": complaint_default,
                    "critical_keywords": [k.strip() for k in complaint_critical_keywords.split(",") if k.strip()],
                    "high_keywords": [k.strip() for k in complaint_high_keywords.split(",") if k.strip()],
                    "medium_keywords": [k.strip() for k in complaint_medium_keywords.split(",") if k.strip()],
                    "low_keywords": [k.strip() for k in complaint_low_keywords.split(",") if k.strip()],
                }
                st.success("Complaint priority rules saved!")

    with tab5:
        st.header("Analytics")

        tickets_df = load_tickets()
        stats = load_stats()

        if tickets_df.empty:
            st.info("No data available for analytics.")
        else:
            # Classification distribution
            st.subheader("Classification Distribution")
            category_counts = tickets_df["category"].value_counts()
            st.pie_chart(category_counts)

            # Priority distribution
            st.subheader("Priority Distribution")
            priority_counts = tickets_df["priority"].value_counts()
            st.bar_chart(priority_counts)

            # Confidence score histogram
            st.subheader("Confidence Score Distribution")
            st.histogram_chart(tickets_df["confidence"])

            # Stats summary
            st.subheader("Summary Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Tickets", stats.get("total_tickets", 0))
            with col2:
                st.metric("Avg Confidence", f"{stats.get('avg_confidence', 0.0):.2%}")
            with col3:
                latest_metrics = stats.get("latest_metrics")
                if latest_metrics:
                    st.metric("Last Processed", latest_metrics.get("total_processed", 0))


if __name__ == "__main__":
    main()


