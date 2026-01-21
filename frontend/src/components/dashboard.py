"""Dashboard tab component."""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import load_stats, load_tickets
from utils import ensure_status_column


def render_dashboard():
    """Render the dashboard overview tab."""
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
        filter_col1, filter_col2, filter_col3 = st.columns(3)
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
        with filter_col3:
            tickets_df = ensure_status_column(tickets_df)
            quick_status = st.selectbox(
                "Filter by Status",
                ["All"] + list(tickets_df["status"].unique()) if not tickets_df.empty else [],
                key="dashboard_status_filter",
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
        if quick_status != "All" and not tickets_df.empty:
            filtered_dashboard_df = ensure_status_column(filtered_dashboard_df)
            filtered_dashboard_df = filtered_dashboard_df[
                filtered_dashboard_df["status"] == quick_status
            ]

        # Recent tickets table
        st.subheader("Recent Tickets")
        if not filtered_dashboard_df.empty:
            filtered_dashboard_df = ensure_status_column(filtered_dashboard_df)
            display_df = filtered_dashboard_df.head(20)[
                ["ticket_id", "title", "category", "priority", "status", "confidence"]
            ]
            # Format status column
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "status": st.column_config.TextColumn(
                        "Status",
                        help="Ticket status: pending, approved, or rejected",
                    )
                }
            )

            # Category distribution
            st.subheader("Category Distribution")
            category_counts = filtered_dashboard_df["category"].value_counts()
            st.bar_chart(category_counts)

