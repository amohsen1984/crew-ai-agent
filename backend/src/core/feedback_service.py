"""Core service for feedback processing."""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent
sys.path.insert(0, str(backend_src))

from crew import FeedbackCrew

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for processing feedback and managing tickets."""

    def __init__(
        self,
        data_dir: str = "data",
        output_dir: str = "output",
        verbose: bool = False,
    ):
        """Initialize FeedbackService.

        Args:
            data_dir: Directory containing input CSV files.
            output_dir: Directory for output files.
            verbose: Enable verbose logging.
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self._crew: Optional[FeedbackCrew] = None

    @property
    def crew(self) -> FeedbackCrew:
        """Lazy initialization of FeedbackCrew."""
        if self._crew is None:
            self._crew = FeedbackCrew(
                data_dir=str(self.data_dir),
                output_dir=str(self.output_dir),
                verbose=self.verbose,
            )
        return self._crew

    def process_feedback(self) -> Dict:
        """Process feedback and generate tickets.

        Returns:
            Dictionary with processing results.
        """
        try:
            result = self.crew.kickoff()
            return {
                "status": "success",
                "data": result,
            }
        except Exception as e:
            logger.error(f"Error processing feedback: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }

    def get_tickets(self) -> List[Dict]:
        """Get all generated tickets.

        Returns:
            List of ticket dictionaries.
        """
        import pandas as pd

        tickets_file = self.output_dir / "generated_tickets.csv"
        if tickets_file.exists():
            df = pd.read_csv(tickets_file)
            # Ensure status column exists, default to "pending"
            if "status" not in df.columns:
                df["status"] = "pending"
            # Fill any NaN values with "pending"
            df["status"] = df["status"].fillna("pending")
            return df.to_dict(orient="records")
        return []

    def get_metrics(self) -> List[Dict]:
        """Get processing metrics.

        Returns:
            List of metrics dictionaries.
        """
        import pandas as pd

        metrics_file = self.output_dir / "metrics.csv"
        if metrics_file.exists():
            df = pd.read_csv(metrics_file)
            return df.to_dict(orient="records")
        return []

    def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict]:
        """Get a specific ticket by ID.

        Args:
            ticket_id: Ticket ID to retrieve.

        Returns:
            Ticket dictionary or None if not found.
        """
        tickets = self.get_tickets()
        for ticket in tickets:
            if ticket.get("ticket_id") == ticket_id:
                return ticket
        return None

    def update_ticket(
        self, ticket_id: str, updates: Dict
    ) -> Dict:
        """Update a ticket.

        Args:
            ticket_id: Ticket ID to update.
            updates: Dictionary of fields to update.

        Returns:
            Result dictionary with status.
        """
        import pandas as pd

        tickets_file = self.output_dir / "generated_tickets.csv"
        if not tickets_file.exists():
            return {"status": "error", "error": "No tickets file found"}

        df = pd.read_csv(tickets_file)
        ticket_idx = df[df["ticket_id"] == ticket_id].index

        if len(ticket_idx) == 0:
            return {"status": "error", "error": "Ticket not found"}

        # Add missing columns (e.g., status) if they don't exist
        for key in updates.keys():
            if key not in df.columns:
                # Initialize with default value based on column name
                if key == "status":
                    df[key] = "pending"  # Default status for all existing tickets
                else:
                    df[key] = None
                # Fill any NaN values for the new column
                df[key] = df[key].fillna("pending" if key == "status" else None)

        # Update fields
        for key, value in updates.items():
            df.at[ticket_idx[0], key] = value

        df.to_csv(tickets_file, index=False)
        return {"status": "success", "message": "Ticket updated"}

    def save_edit_history(
        self, ticket_id: str, action: str, changes: Dict
    ) -> Dict:
        """Save ticket edit history.

        Args:
            ticket_id: Ticket ID being edited.
            action: Action taken (approve/reject/edit).
            changes: Dictionary of changes made.

        Returns:
            Result dictionary with status.
        """
        import json
        from datetime import datetime

        history_file = self.output_dir / "edit_history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing history
        history_data = []
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    history_data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load edit history: {e}")
                history_data = []

        # Add new entry
        edit_entry = {
            "timestamp": datetime.now().isoformat(),
            "ticket_id": ticket_id,
            "action": action,
            "changes": changes,
        }
        history_data.append(edit_entry)

        # Save to file
        try:
            with open(history_file, "w") as f:
                json.dump(history_data, f, indent=2)
            return {"status": "success", "message": "Edit history saved"}
        except Exception as e:
            logger.error(f"Error saving edit history: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

