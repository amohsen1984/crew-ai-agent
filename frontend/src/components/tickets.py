"""Generated Tickets tab component."""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import load_tickets
from utils import ensure_status_column


def render_tickets():
    """Render the generated tickets tab."""
    st.header("Generated Tickets")

    tickets_df = load_tickets()

    if tickets_df.empty:
        st.info("No tickets available.")
    else:
        tickets_df = ensure_status_column(tickets_df)
        
        # Filters
        col1, col2, col3 = st.columns(3)
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
        with col3:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All"] + list(tickets_df["status"].unique()),
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
        if status_filter != "All":
            filtered_df = filtered_df[
                filtered_df["status"] == status_filter
            ]

        # Ensure status column exists and format it
        filtered_df = ensure_status_column(filtered_df)
        
        # Reorder columns to make status more visible (put it after priority)
        column_order = ["ticket_id", "title", "category", "priority", "status"]
        # Add remaining columns that aren't in the order list
        remaining_cols = [col for col in filtered_df.columns if col not in column_order]
        final_column_order = column_order + remaining_cols
        
        # Reorder dataframe columns
        filtered_df = filtered_df[final_column_order]
        
        # Format status column with badges using st.dataframe with column_config
        st.dataframe(
            filtered_df,
            use_container_width=True,
            column_config={
                "status": st.column_config.TextColumn(
                    "Status",
                    help="Ticket status: pending, approved, or rejected",
                )
            }
        )

