"""Background job manager for async processing."""

import logging
import threading
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobManager:
    """Manages background processing jobs."""

    def __init__(self):
        """Initialize JobManager."""
        self._jobs: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def create_job(self) -> str:
        """Create a new job and return its ID.

        Returns:
            Job ID string.
        """
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": JobStatus.PENDING,
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "progress": 0,
                "message": "Job created, waiting to start...",
                "result": None,
                "error": None,
            }
        logger.info(f"Created job {job_id}")
        return job_id

    def start_job(self, job_id: str, target_func, *args, **kwargs) -> None:
        """Start a job in a background thread.

        Args:
            job_id: Job ID.
            target_func: Function to run in background.
            *args: Positional arguments for target_func.
            **kwargs: Keyword arguments for target_func.
        """
        with self._lock:
            if job_id not in self._jobs:
                raise ValueError(f"Job {job_id} not found")
            self._jobs[job_id]["status"] = JobStatus.RUNNING
            self._jobs[job_id]["started_at"] = datetime.now().isoformat()
            self._jobs[job_id]["message"] = "Processing started..."

        def run_job():
            """Run the job and update status."""
            try:
                logger.info(f"Starting job {job_id}")
                result = target_func(*args, **kwargs)

                with self._lock:
                    self._jobs[job_id]["status"] = JobStatus.COMPLETED
                    self._jobs[job_id]["completed_at"] = datetime.now().isoformat()
                    self._jobs[job_id]["progress"] = 100
                    self._jobs[job_id]["message"] = "Processing completed successfully"
                    self._jobs[job_id]["result"] = result

                logger.info(f"Job {job_id} completed successfully")
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}", exc_info=True)
                with self._lock:
                    self._jobs[job_id]["status"] = JobStatus.FAILED
                    self._jobs[job_id]["completed_at"] = datetime.now().isoformat()
                    self._jobs[job_id]["message"] = f"Processing failed: {str(e)}"
                    self._jobs[job_id]["error"] = str(e)

        thread = threading.Thread(target=run_job, daemon=True)
        thread.start()

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job status.

        Args:
            job_id: Job ID.

        Returns:
            Job dictionary or None if not found.
        """
        with self._lock:
            return self._jobs.get(job_id)

    def update_progress(self, job_id: str, progress: int, message: str = None) -> None:
        """Update job progress.

        Args:
            job_id: Job ID.
            progress: Progress percentage (0-100).
            message: Optional progress message.
        """
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["progress"] = min(100, max(0, progress))
                if message:
                    self._jobs[job_id]["message"] = message

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed/failed jobs.

        Args:
            max_age_hours: Maximum age in hours for jobs to keep.

        Returns:
            Number of jobs cleaned up.
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        cleaned = 0

        with self._lock:
            jobs_to_remove = []
            for job_id, job in self._jobs.items():
                if job["status"] in (JobStatus.COMPLETED, JobStatus.FAILED):
                    completed_at = job.get("completed_at")
                    if completed_at:
                        try:
                            completed_timestamp = datetime.fromisoformat(
                                completed_at
                            ).timestamp()
                            if completed_timestamp < cutoff_time:
                                jobs_to_remove.append(job_id)
                        except (ValueError, TypeError):
                            pass

            for job_id in jobs_to_remove:
                del self._jobs[job_id]
                cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old jobs")
        return cleaned


# Global job manager instance
job_manager = JobManager()


