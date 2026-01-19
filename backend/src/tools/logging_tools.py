"""Logging tools for processing tracking."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from crewai.tools import tool

logger = logging.getLogger(__name__)


@tool("Log Processing Action")
def log_processing_tool(
    log_file_path: str,
    source_id: str,
    agent: str,
    action: str,
    result: str,
    confidence: Optional[float] = None,
) -> str:
    """Logs a processing action to the processing log CSV file.

    This tool records agent actions and decisions for traceability and debugging.
    Creates the log file if it doesn't exist.

    Args:
        log_file_path: Path to the processing log CSV file.
        source_id: ID of the feedback being processed.
        agent: Name of the agent performing the action.
        action: Action taken (e.g., 'classified', 'analyzed', 'created_ticket').
        result: Outcome or decision made.
        confidence: Optional confidence score for the action.

    Returns:
        Success message or error message if logging fails.
    """
    try:
        path = Path(log_file_path)
        log_entry = {
            "log_id": f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "timestamp": datetime.now().isoformat(),
            "source_id": source_id,
            "agent": agent,
            "action": action,
            "result": result,
            "confidence": confidence if confidence is not None else "",
        }

        if path.exists():
            df = pd.read_csv(path)
            df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
        else:
            df = pd.DataFrame([log_entry])

        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        logger.debug(f"Logged action: {agent} - {action} for {source_id}")

        return json.dumps(
            {
                "success": True,
                "message": f"Logged action: {agent} - {action} for {source_id}",
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Error logging processing action: {e}", exc_info=True)
        return json.dumps({"error": f"Failed to log action: {str(e)}"}, indent=2)

