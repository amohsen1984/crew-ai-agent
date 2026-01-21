"""Manual Override tab component."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import load_tickets, save_ticket_edit, update_ticket


def render_manual_override():
    """Render the manual override tab."""
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
                
                # Show current status
                current_status = selected_ticket.get("status", "pending")
                status_color = {
                    "pending": "🟡",
                    "approved": "🟢",
                    "rejected": "🔴"
                }
                st.info(f"Current Status: {status_color.get(current_status, '🟡')} {current_status.title()}")

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
                        "status": "approved",
                    }
                    result = update_ticket(selected_ticket_id, changes)
                    if result.get("status") == "success":
                        save_ticket_edit(
                            selected_ticket_id, "approve", changes
                        )
                        st.success(f"Ticket {selected_ticket_id} approved!")
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")

                if reject_btn:
                    changes = {"status": "rejected"}
                    result = update_ticket(selected_ticket_id, changes)
                    if result.get("status") == "success":
                        save_ticket_edit(
                            selected_ticket_id, "reject", changes
                        )
                        st.warning(f"Ticket {selected_ticket_id} rejected!")
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")

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
                            selected_ticket_id, "edit", changes
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

