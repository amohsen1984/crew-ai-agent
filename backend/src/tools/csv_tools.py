"""CSV read/write tools for agents."""

import json
import logging
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from crewai.tools import tool

logger = logging.getLogger(__name__)

# Thread lock for safe concurrent CSV writes
_csv_write_lock = threading.Lock()


@tool("Read CSV File")
def read_csv_tool(file_path: str) -> str:
    """Reads and parses a CSV file, returning structured data as JSON.

    This tool reads CSV files and returns the data in a structured JSON format
    that can be easily processed by agents. Handles errors gracefully.

    Args:
        file_path: Path to the CSV file to read.

    Returns:
        JSON string containing list of records, or error message if file cannot be read.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return json.dumps(
                {"error": f"File not found: {file_path}"}, indent=2
            )

        df = pd.read_csv(file_path)
        if df.empty:
            return json.dumps(
                {"message": "CSV file is empty", "records": []}, indent=2
            )

        records = df.to_dict(orient="records")
        return json.dumps({"records": records, "count": len(records)}, indent=2)

    except pd.errors.EmptyDataError:
        return json.dumps(
            {"error": "CSV file is empty or invalid"}, indent=2
        )
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {e}", exc_info=True)
        return json.dumps(
            {"error": f"Failed to read CSV: {str(e)}"}, indent=2
        )


@tool("Write CSV File")
def write_csv_tool(file_path: str, data: str, append: bool = False) -> str:
    """Writes structured data to a CSV file.

    This tool writes data to CSV files, optionally appending to existing files.
    Data should be provided as a JSON string containing a list of records.

    Args:
        file_path: Path to the output CSV file.
        data: JSON string containing list of records to write.
        append: If True, append to existing file. If False, overwrite.

    Returns:
        Success message with row count, or error message if write fails.
    """
    try:
        path = Path(file_path)
        data_dict = json.loads(data)

        if isinstance(data_dict, dict) and "records" in data_dict:
            records = data_dict["records"]
        elif isinstance(data_dict, list):
            records = data_dict
        else:
            logger.error(f"Invalid data format: {type(data_dict)}")
            return json.dumps(
                {"error": "Invalid data format. Expected list or dict with 'records' key"},
                indent=2,
            )

        if not records:
            logger.warning("No records to write")
            return json.dumps({"error": "No data to write"}, indent=2)

        # Ensure required fields for tickets
        # Check if this is a tickets file by checking if records have ticket_id
        is_tickets_file = "generated_tickets.csv" in str(path) or any(
            "ticket_id" in record for record in records
        )
        
        if is_tickets_file:
            # Ensure status and created_at fields exist for ticket records
            # Generate ticket_id if missing (agents shouldn't generate UUIDs)
            for record in records:
                if "status" not in record:
                    record["status"] = "pending"
                if "created_at" not in record:
                    record["created_at"] = datetime.now().isoformat()
                # Always generate ticket_id in code to ensure uniqueness
                if "ticket_id" not in record or not record.get("ticket_id"):
                    record["ticket_id"] = str(uuid.uuid4())
                    logger.debug(f"Generated ticket_id for record: {record.get('source_id', 'unknown')}")

        df = pd.DataFrame(records)

        # Use thread lock for safe concurrent writes
        with _csv_write_lock:
            if append and path.exists():
                existing_df = pd.read_csv(path)
                # Ensure status column exists in existing data
                if is_tickets_file:
                    if "status" not in existing_df.columns:
                        existing_df["status"] = "pending"
                    else:
                        # Fill any missing status values in existing data
                        existing_df["status"] = existing_df["status"].fillna("pending")

                    # Check for duplicates by ticket_id and regenerate if found
                    if "ticket_id" in df.columns and "ticket_id" in existing_df.columns:
                        existing_ticket_ids = set(existing_df["ticket_id"].tolist())
                        duplicate_mask = df["ticket_id"].isin(existing_ticket_ids)
                        duplicate_count = duplicate_mask.sum()
                        
                        if duplicate_count > 0:
                            logger.warning(
                                f"Found {duplicate_count} duplicate ticket_id(s). Regenerating..."
                            )
                            # Regenerate ticket_ids for duplicates
                            for idx in df[duplicate_mask].index:
                                new_ticket_id = str(uuid.uuid4())
                                # Ensure new ID is also unique within the new records
                                while new_ticket_id in existing_ticket_ids or new_ticket_id in df["ticket_id"].tolist():
                                    new_ticket_id = str(uuid.uuid4())
                                df.at[idx, "ticket_id"] = new_ticket_id
                                logger.info(
                                    f"Regenerated ticket_id for duplicate: "
                                    f"source_id={df.at[idx, 'source_id'] if 'source_id' in df.columns else 'unknown'}, "
                                    f"new_id={new_ticket_id}"
                                )

                    # Check for duplicates by source_id and update instead of append
                    if "source_id" in df.columns and "source_id" in existing_df.columns:
                        new_source_ids = set(df["source_id"].tolist())
                        # Keep existing records that are NOT in the new records
                        existing_df = existing_df[~existing_df["source_id"].isin(new_source_ids)]
                        logger.info(f"Updating {len(new_source_ids)} tickets (replacing existing)")

                df = pd.concat([existing_df, df], ignore_index=True)

            path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(path, index=False)
            logger.info(f"Wrote {len(df)} rows to {file_path}")

        return json.dumps(
            {
                "success": True,
                "message": f"Successfully wrote {len(df)} rows to {file_path}",
                "rows": len(df),
            },
            indent=2,
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in write_csv_tool: {e}", exc_info=True)
        return json.dumps({"error": f"Invalid JSON format: {str(e)}"}, indent=2)
    except Exception as e:
        logger.error(f"Error writing CSV file {file_path}: {e}", exc_info=True)
        return json.dumps({"error": f"Failed to write CSV: {str(e)}"}, indent=2)

