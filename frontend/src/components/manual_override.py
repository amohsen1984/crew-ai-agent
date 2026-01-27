"""Manual Override tab component."""

import sys
import time
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

        # Batch approval/rejection
        st.subheader("Batch Approval/Rejection")
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

                if len(batch_tickets) > 0:
                    col_approve, col_reject = st.columns(2)
                    
                    with col_approve:
                        if st.button("✅ Approve All Matching", type="primary", key="batch_approve"):
                            approved_count = 0
                            failed_count = 0
                            error_messages = []
                            failed_ticket_ids = []
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            total_tickets = len(batch_tickets)
                            
                            with st.spinner(f"Approving {total_tickets} tickets..."):
                                for idx, (_, ticket) in enumerate(batch_tickets.iterrows(), 1):
                                    ticket_id = ticket["ticket_id"]
                                    status_text.text(f"Processing ticket {idx}/{total_tickets}: {ticket_id}")
                                    progress_bar.progress(idx / total_tickets)
                                    
                                    changes = {
                                        "status": "approved",
                                        "category": batch_category if batch_category != "All" else ticket["category"],
                                        "priority": batch_priority if batch_priority != "All" else ticket["priority"],
                                    }
                                    
                                    # Retry logic for race conditions
                                    max_retries = 5
                                    retry_delay = 0.3  # 300ms delay between retries
                                    success = False
                                    last_error = None
                                    
                                    for attempt in range(max_retries):
                                        result = update_ticket(ticket_id, changes)
                                        
                                        # Check if result is valid and successful
                                        if result:
                                            if result.get("status") == "success":
                                                # Small delay for file system sync
                                                time.sleep(0.15)
                                                approved_count += 1
                                                save_ticket_edit(ticket_id, "approve", changes)
                                                success = True
                                                break
                                            else:
                                                last_error = result.get("error", "Unknown error")
                                        else:
                                            last_error = "API request returned None"
                                        
                                        # Wait before retry (exponential backoff)
                                        if attempt < max_retries - 1:
                                            time.sleep(retry_delay * (attempt + 1))
                                    
                                    if not success:
                                        failed_count += 1
                                        failed_ticket_ids.append(ticket_id)
                                        error_msg = last_error or "Update failed after retries"
                                        error_messages.append(f"Ticket {ticket_id}: {error_msg}")
                                    
                                    # Delay between tickets to reduce race conditions
                                    if idx < total_tickets:
                                        time.sleep(0.25)  # Increased delay for better reliability
                            
                            progress_bar.empty()
                            status_text.empty()
                            
                            if approved_count > 0:
                                st.success(f"✅ Approved {approved_count} ticket(s)!")
                            if failed_count > 0:
                                st.error(f"❌ Failed to approve {failed_count} ticket(s)")
                                if error_messages:
                                    with st.expander("Error details"):
                                        st.write("**Failed tickets:**")
                                        for ticket_id in failed_ticket_ids:
                                            st.text(f"- {ticket_id}")
                                        st.write("**Error messages:**")
                                        for msg in error_messages:
                                            st.text(msg)
                            
                            if approved_count > 0:
                                st.rerun()
                    
                    with col_reject:
                        if st.button("❌ Reject All Matching", key="batch_reject"):
                            rejected_count = 0
                            failed_count = 0
                            error_messages = []
                            failed_ticket_ids = []
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            total_tickets = len(batch_tickets)
                            
                            with st.spinner(f"Rejecting {total_tickets} tickets..."):
                                for idx, (_, ticket) in enumerate(batch_tickets.iterrows(), 1):
                                    ticket_id = ticket["ticket_id"]
                                    status_text.text(f"Processing ticket {idx}/{total_tickets}: {ticket_id}")
                                    progress_bar.progress(idx / total_tickets)
                                    
                                    changes = {"status": "rejected"}
                                    
                                    # Retry logic for race conditions
                                    max_retries = 5
                                    retry_delay = 0.3  # 300ms delay between retries
                                    success = False
                                    last_error = None
                                    
                                    for attempt in range(max_retries):
                                        result = update_ticket(ticket_id, changes)
                                        
                                        # Check if result is valid and successful
                                        if result:
                                            if result.get("status") == "success":
                                                # Small delay for file system sync
                                                time.sleep(0.15)
                                                rejected_count += 1
                                                save_ticket_edit(ticket_id, "reject", changes)
                                                success = True
                                                break
                                            else:
                                                last_error = result.get("error", "Unknown error")
                                        else:
                                            last_error = "API request returned None"
                                        
                                        # Wait before retry (exponential backoff)
                                        if attempt < max_retries - 1:
                                            time.sleep(retry_delay * (attempt + 1))
                                    
                                    if not success:
                                        failed_count += 1
                                        failed_ticket_ids.append(ticket_id)
                                        error_msg = last_error or "Update failed after retries"
                                        error_messages.append(f"Ticket {ticket_id}: {error_msg}")
                                    
                                    # Delay between tickets to reduce race conditions
                                    if idx < total_tickets:
                                        time.sleep(0.25)  # Increased delay for better reliability
                            
                            progress_bar.empty()
                            status_text.empty()
                            
                            if rejected_count > 0:
                                st.warning(f"❌ Rejected {rejected_count} ticket(s)!")
                            if failed_count > 0:
                                st.error(f"❌ Failed to reject {failed_count} ticket(s)")
                                if error_messages:
                                    with st.expander("Error details"):
                                        st.write("**Failed tickets:**")
                                        for ticket_id in failed_ticket_ids:
                                            st.text(f"- {ticket_id}")
                                        st.write("**Error messages:**")
                                        for msg in error_messages:
                                            st.text(msg)
                            
                            if rejected_count > 0:
                                st.rerun()

        st.divider()

        # Edit history log
        st.subheader("Edit History")
        if st.session_state.edit_history:
            history_df = pd.DataFrame(st.session_state.edit_history)
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("No edit history yet.")

