"""Processing status and polling component."""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from api_client import get_process_status, start_process_feedback
from components.js_utils import (
    setup_auto_refresh,
    clear_auto_refresh,
    load_job_id_from_storage,
    store_job_id_in_storage,
    clear_job_id_from_storage,
)


def render_processing_status():
    """Render processing status indicator and controls."""
    st.subheader("Processing Status")
    status_emoji = {
        "idle": "⚪",
        "pending": "🟡",
        "running": "🟡",
        "processing": "🟡",
        "completed": "🟢",
        "failed": "🔴",
        "error": "🔴",
    }
    
    # Load job_id from localStorage on page load if not in session state
    # Check query params first (may have been set by JavaScript)
    query_params = st.query_params
    if "job_id" in query_params and ("processing_job_id" not in st.session_state or not st.session_state.processing_job_id):
        job_id = query_params["job_id"]
        if isinstance(job_id, list):
            job_id = job_id[0]
        st.session_state.processing_job_id = job_id
    
    # If no job_id in session state, use JavaScript to read from localStorage and set query param
    if "processing_job_id" not in st.session_state or not st.session_state.processing_job_id:
        load_job_id_from_storage()
    
    # Fetch job status when page loads if there's an active job
    if st.session_state.processing_job_id:
        job_id = st.session_state.processing_job_id
        job_status = get_process_status(job_id)
        
        # Update session state based on fetched status
        if job_status.get("status") == "running":
            st.session_state.processing_status = "running"
            st.session_state.processing_progress = job_status.get("progress", 0)
            st.session_state.processing_message = job_status.get("message", "N/A")
        elif job_status.get("status") == "completed":
            st.session_state.processing_status = "completed"
            st.session_state.processing_progress = 100
            st.session_state.processing_job_id = None
            clear_job_id_from_storage(reason="completed")
        elif job_status.get("status") == "failed":
            st.session_state.processing_status = "failed"
            st.session_state.processing_job_id = None
            clear_job_id_from_storage(reason="failed")
        elif job_status.get("status") == "not_found":
            # Job no longer exists (backend restarted or cleaned up)
            # Silently reset to idle state
            st.session_state.processing_status = "idle"
            st.session_state.processing_job_id = None
            st.session_state.processing_progress = 0
            st.session_state.processing_message = ""
            clear_job_id_from_storage(reason="not_found")
    
    status = st.session_state.processing_status
    st.write(f"{status_emoji.get(status, '⚪')} {status.capitalize()}")
    
    # Show progress if processing
    if status in ["pending", "running", "processing"]:
        progress = st.session_state.processing_progress
        message = st.session_state.processing_message

        # Progress bar with percentage
        col1, col2 = st.columns([4, 1])
        with col1:
            st.progress(progress / 100)
        with col2:
            st.write(f"**{progress}%**")

        # Current item being processed
        if message:
            st.info(f"📝 {message}")
    
    # Show completion message if completed
    if status == "completed":
        st.success("✅ Processing completed successfully!")
    
    # Show error message if failed
    if status == "failed":
        st.error("❌ Processing failed")
    
    # Process button
    if st.button("🚀 Process Feedback", type="primary", disabled=status in ["pending", "running", "processing"]):
        result = start_process_feedback()
        if result.get("status") == "started" and result.get("job_id"):
            job_id = result["job_id"]
            st.session_state.processing_job_id = job_id
            st.session_state.processing_status = "pending"
            st.session_state.processing_progress = 0
            st.session_state.processing_message = "Job started, waiting for processing..."
            st.success(f"Processing started! Job ID: {job_id[:8]}...")
            store_job_id_in_storage(job_id)
            setup_auto_refresh(interval_seconds=5, source="button-press", job_id=job_id)
        else:
            error_msg = result.get('error', 'Unknown error')
            st.error(f"Failed to start processing: {error_msg}")
    
    # Refresh button - always visible
    if st.button("🔄 Refresh", key="refresh", help="Auto-refresh every 30 seconds"):
        st.rerun()
    
    # Auto-refresh every 30 seconds when job is active
    if st.session_state.processing_job_id:
        job_id = st.session_state.processing_job_id
        # Update query params with job_id if not already set
        if "job_id" not in st.query_params or st.query_params["job_id"] != job_id:
            st.query_params["job_id"] = job_id
        
        # Only setup auto-refresh if status is active
        if status in ["pending", "running", "processing"]:
            setup_auto_refresh(interval_seconds=5, source="initial-render", job_id=job_id)
        else:
            clear_auto_refresh()
    else:
        clear_auto_refresh()

