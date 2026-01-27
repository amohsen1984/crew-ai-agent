"""FastAPI application for feedback processing backend."""

import logging
import math
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent
sys.path.insert(0, str(backend_src))

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.feedback_service import FeedbackService
from core.job_manager import job_manager, JobStatus

# Suppress CrewAI telemetry warnings
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "1"
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*signal.*")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("crewai.telemetry").setLevel(logging.ERROR)

def _sanitize_value(value: Any) -> Any:
    """Recursively sanitize values for JSON serialization (handles NaN, Infinity)."""
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value


def _sanitize_dict(d: Dict) -> Dict:
    """Recursively sanitize all values in a dictionary for JSON serialization."""
    if d is None:
        return None
    return {k: _sanitize_value(v) for k, v in d.items()}


# Validate OpenAI API key at startup
def _validate_openai_api_key():
    """Validate OpenAI API key format at startup."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set!")
        raise ValueError("OPENAI_API_KEY must be set in .env file or environment")
    
    # Check for common copy-paste error
    if api_key.startswith("OPENAI_API_KEY="):
        logger.error(
            f"Invalid API key format detected. "
            f"The key appears to include the variable name. "
            f"First 50 chars: {api_key[:50]}..."
        )
        raise ValueError(
            "OPENAI_API_KEY appears malformed. "
            "Check your .env file - it should be: OPENAI_API_KEY=sk-... "
            "(not OPENAI_API_KEY=OPENAI_API_KEY=sk-...)"
        )
    
    if not api_key.startswith("sk-"):
        logger.warning(
            f"OpenAI API key doesn't start with 'sk-'. "
            f"First 10 chars: {api_key[:10]}..."
        )
    
    logger.info(f"OpenAI API key validated (starts with: {api_key[:7]}...)")

# Validate API key at startup
try:
    _validate_openai_api_key()
except ValueError as e:
    logger.error(f"API key validation failed: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(
    title="Feedback Analysis API",
    description="API for processing user feedback into structured tickets",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
service = FeedbackService(
    data_dir=os.getenv("DATA_DIR", "data"),
    output_dir=os.getenv("OUTPUT_DIR", "output"),
    verbose=os.getenv("VERBOSE", "false").lower() == "true",
)


# Pydantic models for API
class ProcessFeedbackResponse(BaseModel):
    """Response model for process feedback endpoint."""

    status: str
    job_id: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict] = None
    error: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Response model for job status endpoint."""

    job_id: str
    status: str
    progress: int
    message: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


class TicketResponse(BaseModel):
    """Response model for ticket."""

    ticket_id: str
    source_id: str
    source_type: str
    title: str
    category: str
    priority: str
    description: str
    technical_details: Optional[str] = None
    confidence: float
    status: str = "pending"
    created_at: str


class TicketUpdate(BaseModel):
    """Model for ticket updates."""

    title: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    technical_details: Optional[str] = None
    status: Optional[str] = None


class EditHistoryRequest(BaseModel):
    """Model for edit history entry."""

    ticket_id: str
    action: str
    changes: Dict


# Priority rules are sent as a dictionary, so we'll accept it directly
# Using Dict[str, Any] instead of a BaseModel to handle "Feature Request" key with space


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Feedback Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "process": "/api/v1/process",
            "process_status": "/api/v1/process/status/{job_id}",
            "tickets": "/api/v1/tickets",
            "metrics": "/api/v1/metrics",
            "health": "/api/v1/health",
        },
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def _process_feedback_background(job_id: str) -> Dict:
    """Background function to process feedback.

    Args:
        job_id: Job ID for progress tracking.

    Returns:
        Processing result dictionary.
    """
    try:
        job_manager.update_progress(job_id, 5, "Loading feedback data...")

        # Create progress callback that updates job_manager
        def progress_callback(progress: int, message: str):
            job_manager.update_progress(job_id, progress, message)

        result = service.process_feedback(progress_callback=progress_callback)

        if result.get("status") == "success":
            job_manager.update_progress(job_id, 95, "Processing completed successfully")
            return result
        else:
            raise Exception(result.get("error", "Unknown error"))
    except Exception as e:
        logger.error(f"Error in background processing: {e}", exc_info=True)
        raise


@app.post("/api/v1/process", response_model=ProcessFeedbackResponse)
async def process_feedback():
    """Start processing feedback from CSV files in background.

    Returns:
        Job information with job_id for status polling.
    """
    try:
        # Create a new job
        job_id = job_manager.create_job()
        
        # Start processing in background
        job_manager.start_job(job_id, _process_feedback_background, job_id)
        
        return ProcessFeedbackResponse(
            status="started",
            job_id=job_id,
            message="Processing started in background. Use /api/v1/process/status/{job_id} to check status.",
        )
    except Exception as e:
        logger.error(f"Error starting process_feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/process/status/{job_id}", response_model=JobStatusResponse)
async def get_process_status(job_id: str):
    """Get the status of a processing job.

    Args:
        job_id: Job ID returned from /api/v1/process.

    Returns:
        Job status information.
    """
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobStatusResponse(**job)


@app.get("/api/v1/tickets", response_model=List[TicketResponse])
async def get_tickets(
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected)"),
    limit: int = Query(100, ge=1, le=1000, description="Limit number of results"),
):
    """Get all generated tickets with optional filtering.

    Args:
        category: Filter by category (Bug, Feature Request, etc.).
        priority: Filter by priority (Critical, High, Medium, Low).
        status: Filter by status (pending, approved, rejected).
        limit: Maximum number of tickets to return.

    Returns:
        List of tickets.
    """
    try:
        tickets = service.get_tickets()

        # Apply filters
        if category:
            tickets = [t for t in tickets if t.get("category") == category]
        if priority:
            tickets = [t for t in tickets if t.get("priority") == priority]
        if status:
            tickets = [t for t in tickets if t.get("status", "pending") == status.lower()]

        # Limit results
        tickets = tickets[:limit]

        # Sanitize tickets to handle NaN/Infinity values
        return [_sanitize_dict(t) for t in tickets]
    except Exception as e:
        logger.error(f"Error in get_tickets endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    """Get a specific ticket by ID.

    Args:
        ticket_id: Ticket ID.

    Returns:
        Ticket details.
    """
    try:
        ticket = service.get_ticket_by_id(ticket_id)
        if ticket is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        # Sanitize ticket to handle NaN/Infinity values
        return _sanitize_dict(ticket)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_ticket endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/v1/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, updates: TicketUpdate):
    """Update a ticket.

    Args:
        ticket_id: Ticket ID to update.
        updates: Fields to update.

    Returns:
        Update result.
    """
    try:
        update_dict = updates.model_dump(exclude_unset=True)
        result = service.update_ticket(ticket_id, update_dict)
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_ticket endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics")
async def get_metrics():
    """Get processing metrics.

    Returns:
        List of metrics.
    """
    try:
        metrics = service.get_metrics()
        # Sanitize metrics to handle NaN/Infinity values
        sanitized_metrics = [_sanitize_dict(m) for m in metrics]
        return {"metrics": sanitized_metrics}
    except Exception as e:
        logger.error(f"Error in get_metrics endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tickets/{ticket_id}/history")
async def save_edit_history(ticket_id: str, request: EditHistoryRequest):
    """Save ticket edit history.

    Args:
        ticket_id: Ticket ID being edited.
        request: Edit history entry data.

    Returns:
        Success message.
    """
    try:
        result = service.save_edit_history(
            ticket_id=ticket_id,
            action=request.action,
            changes=request.changes,
        )
        return result
    except Exception as e:
        logger.error(f"Error saving edit history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats")
async def get_stats():
    """Get summary statistics.

    Returns:
        Summary statistics.
    """
    try:
        tickets = service.get_tickets()
        metrics = service.get_metrics()

        if not tickets:
            return {
                "total_tickets": 0,
                "by_category": {},
                "by_priority": {},
                "avg_confidence": 0.0,
            }

        # Calculate stats
        categories = {}
        priorities = {}
        confidences = []

        for ticket in tickets:
            cat = ticket.get("category", "Unknown")
            pri = ticket.get("priority", "Unknown")
            conf = ticket.get("confidence")

            categories[cat] = categories.get(cat, 0) + 1
            priorities[pri] = priorities.get(pri, 0) + 1
            # Only add valid float values (not None, NaN, or Infinity)
            if conf is not None:
                try:
                    conf_float = float(conf)
                    if not math.isnan(conf_float) and not math.isinf(conf_float):
                        confidences.append(conf_float)
                except (ValueError, TypeError):
                    pass

        avg_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )

        # Sanitize metrics data to handle any NaN/Infinity values
        latest_metrics = None
        if metrics:
            latest_metrics = _sanitize_dict(metrics[-1])

        return {
            "total_tickets": len(tickets),
            "by_category": categories,
            "by_priority": priorities,
            "avg_confidence": avg_confidence,
            "latest_metrics": latest_metrics,
        }
    except Exception as e:
        logger.error(f"Error in get_stats endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/expected-classifications")
async def get_expected_classifications():
    """Get expected classifications for QA comparison.

    Returns:
        List of expected classifications.
    """
    try:
        expected = service.get_expected_classifications()
        # Sanitize to handle NaN/Infinity values
        return [_sanitize_dict(e) for e in expected]
    except Exception as e:
        logger.error(f"Error in get_expected_classifications endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/priority-rules")
async def set_priority_rules(rules: Dict[str, Any]):
    """Set priority rules configuration.

    Args:
        rules: Priority rules for each category (dict with keys like "Bug", "Feature Request", "Complaint").

    Returns:
        Success message.
    """
    try:
        result = service.set_priority_rules(rules)
        return result
    except Exception as e:
        logger.error(f"Error setting priority rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/priority-rules")
async def get_priority_rules():
    """Get current priority rules configuration.

    Returns:
        Current priority rules.
    """
    try:
        rules = service.get_priority_rules()
        return rules
    except Exception as e:
        logger.error(f"Error getting priority rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tickets/deduplicate")
async def deduplicate_tickets():
    """Remove duplicate tickets by regenerating ticket_ids for duplicates.

    Returns:
        Deduplication result with statistics.
    """
    try:
        result = service.deduplicate_tickets()
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in deduplicate_tickets endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

