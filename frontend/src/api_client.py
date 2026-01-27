"""API client for backend communication."""

import logging
import os
from typing import Dict, Optional

import requests
import streamlit as st

logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")


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
        result = response.json()
        # Log if result indicates an error
        if isinstance(result, dict) and result.get("status") == "error":
            logger.warning(f"API returned error status: {result.get('error', 'Unknown error')}")
        return result
    except requests.exceptions.HTTPError as e:
        # Try to get error details from response
        try:
            error_detail = e.response.json() if e.response else {}
            logger.error(f"API HTTP error {e.response.status_code}: {error_detail}")
        except:
            logger.error(f"API HTTP error {e.response.status_code}: {str(e)}")
        return {"status": "error", "error": f"HTTP {e.response.status_code}: {str(e)}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return {"status": "error", "error": f"Request failed: {str(e)}"}


def load_tickets() -> "pd.DataFrame":
    """Load generated tickets from API.

    Returns:
        DataFrame with tickets or empty DataFrame.
    """
    import pandas as pd
    
    response = api_request("GET", "/api/v1/tickets", params={"limit": 1000})
    if response:
        return pd.DataFrame(response)
    return pd.DataFrame()


def load_metrics() -> "pd.DataFrame":
    """Load metrics from API.

    Returns:
        DataFrame with metrics or empty DataFrame.
    """
    import pandas as pd
    
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


def load_expected_classifications() -> "pd.DataFrame":
    """Load expected classifications for QA comparison.

    Returns:
        DataFrame with expected classifications or empty DataFrame.
    """
    import pandas as pd

    response = api_request("GET", "/api/v1/expected-classifications")
    if response:
        return pd.DataFrame(response)
    return pd.DataFrame()


def start_process_feedback() -> Dict:
    """Start processing feedback via API (returns immediately with job_id).

    Returns:
        Response dictionary with job_id.
    """
    response = api_request("POST", "/api/v1/process")
    return response or {"status": "error", "error": "API request failed"}


def get_process_status(job_id: str) -> Dict:
    """Get processing job status.

    Args:
        job_id: Job ID from start_process_feedback.

    Returns:
        Job status dictionary.
    """
    url = f"{API_BASE_URL}/api/v1/process/status/{job_id}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 404:
            # Job not found - likely cleaned up or backend restarted
            # This is expected behavior, not an error to display
            logger.info(f"Job {job_id} not found (404) - may have been cleaned up")
            return {"status": "not_found", "message": "Job not found"}
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get job status: {e}")
        st.error(f"API Error: {str(e)}")
        return {"status": "error", "error": str(e)}


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


def set_priority_rules(rules: Dict) -> Dict:
    """Set priority rules configuration via API.

    Args:
        rules: Dictionary with priority rules for each category.

    Returns:
        Response dictionary with status.
    """
    response = api_request("POST", "/api/v1/priority-rules", json=rules)
    return response or {"status": "error", "error": "API request failed"}


def get_priority_rules() -> Dict:
    """Get current priority rules configuration from API.

    Returns:
        Dictionary with priority rules or empty dict on error.
    """
    response = api_request("GET", "/api/v1/priority-rules")
    return response or {}


def deduplicate_tickets() -> Dict:
    """Deduplicate tickets by regenerating ticket_ids for duplicates.

    Returns:
        Deduplication result dictionary.
    """
    response = api_request("POST", "/api/v1/tickets/deduplicate")
    return response or {"status": "error", "error": "API request failed"}


def save_ticket_edit(ticket_id: str, action: str, changes: Dict) -> None:
    """Save ticket edit to history via backend API.

    Args:
        ticket_id: Ticket ID being edited.
        action: Action taken (approve/reject/edit).
        changes: Dictionary of changes made.
    """
    from datetime import datetime
    import streamlit as st
    
    # Add to session state for UI display
    edit_entry = {
        "timestamp": datetime.now().isoformat(),
        "ticket_id": ticket_id,
        "action": action,
        "changes": changes,
    }
    if "edit_history" not in st.session_state:
        st.session_state.edit_history = []
    st.session_state.edit_history.append(edit_entry)

    # Save to backend
    response = api_request(
        "POST",
        f"/api/v1/tickets/{ticket_id}/history",
        json={"ticket_id": ticket_id, "action": action, "changes": changes},
    )
    if not response or response.get("status") != "success":
        print(f"Warning: Could not save edit history: {response}")


