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
from core.priority_rules import PriorityRulesManager

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
        self.priority_rules_manager = PriorityRulesManager(self.output_dir)

    @property
    def crew(self) -> FeedbackCrew:
        """Lazy initialization of FeedbackCrew."""
        if self._crew is None:
            self._crew = FeedbackCrew(
                data_dir=str(self.data_dir),
                output_dir=str(self.output_dir),
                verbose=self.verbose,
                priority_rules=self.priority_rules_manager.get_rules(),
            )
        else:
            # Update priority rules if crew already exists
            self._crew.set_priority_rules(
                self.priority_rules_manager.get_rules()
            )
        return self._crew

    def process_feedback(self, progress_callback=None) -> Dict:
        """Process feedback and generate tickets.

        Args:
            progress_callback: Optional callback function(progress, message) for progress updates.

        Returns:
            Dictionary with processing results.
        """
        try:
            result = self.crew.kickoff(progress_callback=progress_callback)
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
            # Convert NaN values to None for Pydantic compatibility
            df = df.where(pd.notna(df), None)
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

    def get_expected_classifications(self) -> List[Dict]:
        """Get expected classifications for QA comparison.

        Returns:
            List of expected classification dictionaries.
        """
        import pandas as pd

        expected_file = self.data_dir / "expected_classifications.csv"
        if expected_file.exists():
            df = pd.read_csv(expected_file)
            # Convert NaN to None for JSON compatibility
            df = df.where(pd.notna(df), None)
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

    def set_priority_rules(self, rules: Dict) -> Dict:
        """Set priority rules configuration.

        Args:
            rules: Dictionary with priority rules for each category (may be partial).

        Returns:
            Result dictionary with status.
        """
        result = self.priority_rules_manager.set_rules(rules)
        
        # Update crew if it exists and save was successful
        if result.get("status") == "success" and self._crew is not None:
            self._crew.set_priority_rules(
                self.priority_rules_manager.get_rules()
            )
        
        return result

    def get_priority_rules(self) -> Dict:
        """Get current priority rules configuration.

        Returns:
            Current priority rules dictionary (with defaults if none set).
        """
        return self.priority_rules_manager.get_rules()