"""Crew orchestration for feedback processing pipeline."""

import ast
import json
import os
import uuid
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

# Suppress CrewAI telemetry warnings
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "1"
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*signal.*")

import pandas as pd
from crewai import Crew, Process, Task
from langchain_openai import ChatOpenAI

from agents import (
    create_bug_analyzer_agent,
    create_classifier_agent,
    create_csv_reader_agent,
    create_fallback_agent,
    create_feature_extractor_agent,
    create_quality_critic_agent,
    create_ticket_creator_agent,
)
from models.feedback import FeedbackInput
from models.ticket import (
    BugAnalysis,
    ClassificationResult,
    FeatureAnalysis,
    TicketOutput,
)


class FeedbackCrew:
    """Crew for processing user feedback into structured tickets."""

    def __init__(
        self,
        data_dir: str = "data",
        output_dir: str = "output",
        verbose: bool = True,
        priority_rules: Optional[Dict] = None,
    ):
        """Initialize FeedbackCrew.

        Args:
            data_dir: Directory containing input CSV files.
            output_dir: Directory for output files.
            verbose: Enable verbose logging.
            priority_rules: Priority rules configuration dictionary.
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.priority_rules = priority_rules or {}

        # Initialize agents
        self.csv_reader = create_csv_reader_agent()
        self.classifier = create_classifier_agent()
        self.bug_analyzer = create_bug_analyzer_agent()
        self.feature_extractor = create_feature_extractor_agent()
        self.ticket_creator = create_ticket_creator_agent()
        self.quality_critic = create_quality_critic_agent()
        self.fallback_agent = create_fallback_agent()

        # Error handling configuration
        self.max_retries = 3

        # Output file paths
        self.tickets_file = self.output_dir / "generated_tickets.csv"
        self.log_file = self.output_dir / "processing_log.csv"
        self.metrics_file = self.output_dir / "metrics.csv"
        self.errors_file = self.output_dir / "processing_errors.csv"

    def set_priority_rules(self, rules: Dict):
        """Update priority rules configuration.

        Args:
            rules: Priority rules configuration dictionary.
        """
        self.priority_rules = rules

    def _format_priority_rules(self) -> str:
        """Format priority rules into a string for task description.

        Returns:
            Formatted priority rules string.
        """
        if not self.priority_rules:
            return ""
        
        rules_text = "\n\nPRIORITY ASSIGNMENT RULES (STRICTLY FOLLOW THESE):\n\n"
        
        for category, rules in self.priority_rules.items():
            rules_text += f"{category.upper()}:\n"
            rules_text += f"- Default Priority: {rules.get('default', 'Medium')}\n"
            
            for priority_level in ["critical", "high", "medium", "low"]:
                keywords_key = f"{priority_level}_keywords"
                keywords = rules.get(keywords_key, [])
                if keywords:
                    keywords_str = ", ".join([f'"{kw}"' for kw in keywords])
                    priority_capitalized = priority_level.capitalize()
                    rules_text += f"- {priority_capitalized} if contains keywords: {keywords_str}\n"
            
            rules_text += "\n"
        
        return rules_text

    def _normalize_feedback(self, row: Dict[str, Any], source_type: str) -> FeedbackInput:
        """Normalize CSV row into FeedbackInput model.

        Args:
            row: CSV row as dictionary.
            source_type: Type of source ('app_store_review' or 'email').

        Returns:
            Normalized FeedbackInput object.
        """
        if source_type == "app_store_review":
            return FeedbackInput(
                source_id=row.get("review_id", ""),
                source_type="app_store_review",
                text=row.get("review_text", ""),
                platform=row.get("platform"),
                rating=row.get("rating"),
                app_version=row.get("app_version"),
                user_name=row.get("user_name"),
                date=row.get("date"),
            )
        else:  # email
            return FeedbackInput(
                source_id=row.get("email_id", ""),
                source_type="email",
                text=row.get("body", ""),
                subject=row.get("subject"),
                sender_email=row.get("sender_email"),
                timestamp=row.get("timestamp"),
                priority=row.get("priority"),
            )

    def _load_feedback_data(self) -> List[FeedbackInput]:
        """Load and normalize feedback from CSV files.

        Returns:
            List of normalized FeedbackInput objects.
        """
        feedback_items = []

        # Load app store reviews
        reviews_path = self.data_dir / "app_store_reviews.csv"
        if reviews_path.exists():
            df_reviews = pd.read_csv(reviews_path)
            for _, row in df_reviews.iterrows():
                try:
                    feedback = self._normalize_feedback(row, "app_store_review")
                    feedback_items.append(feedback)
                except Exception as e:
                    print(f"Warning: Failed to normalize review {row.get('review_id')}: {e}")

        # Load support emails
        emails_path = self.data_dir / "support_emails.csv"
        if emails_path.exists():
            df_emails = pd.read_csv(emails_path)
            for _, row in df_emails.iterrows():
                try:
                    feedback = self._normalize_feedback(row, "email")
                    feedback_items.append(feedback)
                except Exception as e:
                    print(f"Warning: Failed to normalize email {row.get('email_id')}: {e}")

        return feedback_items

    def _create_tasks_for_feedback(
        self, feedback: FeedbackInput
    ) -> List[Task]:
        """Create tasks for processing a single feedback item.

        Args:
            feedback: FeedbackInput object to process.

        Returns:
            List of tasks in processing order.
        """
        # Task 1: Classify feedback
        classify_task = Task(
            description=f"""
            Classify the following user feedback into one category:
            - Bug: Technical issues, crashes, errors, broken functionality
            - Feature Request: New functionality suggestions, enhancements
            - Praise: Positive feedback, compliments
            - Complaint: Non-technical dissatisfaction, pricing issues
            - Spam: Irrelevant or promotional content

            Feedback Text: {feedback.text}
            Source Type: {feedback.source_type}
            Rating: {feedback.rating if feedback.rating else 'N/A'}
            Platform: {feedback.platform if feedback.platform else 'N/A'}
            """,
            expected_output="""
            A JSON object with:
            - category: string (Bug|Feature Request|Praise|Complaint|Spam)
            - confidence: float (0.0-1.0)
            - reasoning: string explaining the classification
            """,
            agent=self.classifier,
            output_json=ClassificationResult,
        )

        # Task 2: Analyze based on classification
        # Use bug analyzer as primary, but task description routes to appropriate analysis
        analyze_task = Task(
            description=f"""
            Based on the classification result from the previous task, analyze the feedback:
            
            IF classified as "Bug":
            Use Bug Analyzer expertise to:
            - Extract steps to reproduce (if mentioned)
            - Identify platform/OS version
            - Extract app version
            - Identify device model (if mentioned)
            - Assess severity: Critical (data loss, security, app unusable), 
              High (major feature broken), Medium (minor bug, workaround exists), 
              Low (cosmetic issue, edge case)
            - Describe affected functionality
            
            IF classified as "Feature Request":
            Use Feature Extractor expertise to:
            - Summarize the requested feature
            - Identify user pain point or motivation
            - Assess impact: High (many users, high intensity), Medium, Low
            - Identify similar existing features (if any)
            - Estimate implementation complexity
            
            IF classified as "Praise", "Complaint", or "Spam":
            Provide minimal analysis or pass-through.
            
            Original Feedback: {feedback.text}
            Source: {feedback.source_type} - {feedback.source_id}
            Platform: {feedback.platform if feedback.platform else 'N/A'}
            App Version: {feedback.app_version if feedback.app_version else 'N/A'}
            """,
            expected_output="""
            For Bugs: JSON with steps_to_reproduce, platform, app_version, 
            device_model, severity, affected_functionality.
            
            For Features: JSON with feature_summary, user_pain_point, impact, 
            similar_features, implementation_complexity.
            
            For other categories: Minimal analysis or pass-through.
            """,
            agent=self.bug_analyzer,  # Primary agent, but will route based on classification
            context=[classify_task],
        )
        
        # Additional feature analysis task that runs in parallel context
        feature_analyze_task = Task(
            description=f"""
            If the classification is "Feature Request", analyze the feature request:
            - Summarize the requested feature
            - Identify user pain point or motivation
            - Assess impact: High (many users, high intensity), Medium, Low
            - Identify similar existing features (if any)
            - Estimate implementation complexity
            
            Original Feedback: {feedback.text}
            """,
            expected_output="""
            JSON with feature_summary, user_pain_point, impact, 
            similar_features, implementation_complexity.
            Only provide output if classification is "Feature Request".
            """,
            agent=self.feature_extractor,
            context=[classify_task],
        )

        # Task 3: Create ticket
        priority_rules_text = self._format_priority_rules()
        create_ticket_task = Task(
            description=f"""
            Create a structured ticket from the classified and analyzed feedback.
            
            Use this template:
            Title: [Category] Brief description
            Priority: [Critical|High|Medium|Low] - based on severity/impact
            Category: [from classification]
            Source: {feedback.source_type} - {feedback.source_id}
            
            Description: Detailed description based on analysis
            Technical Details: (for bugs only) Platform, steps to reproduce, severity
            User Impact: (for features) Impact assessment, user pain point
            
            Original Feedback: {feedback.text}
            {priority_rules_text}
            IMPORTANT: After creating the ticket, you MUST write it to the CSV file using the write_csv_tool.
            Use this EXACT file path (do not modify it): {self.tickets_file}
            Format the ticket data as a JSON object with a "records" key containing a list with one ticket object.
            Set append=True when writing to add to existing tickets.

            Example tool call:
            write_csv_tool(file_path="{self.tickets_file}", data='{{"records": [{{...ticket data...}}]}}', append=True)
            """,
            expected_output="""
            A JSON object with:
            - ticket_id: string (UUID)
            - source_id: string
            - source_type: string
            - title: string
            - category: string
            - priority: string
            - description: string
            - technical_details: string (for bugs)
            - confidence: float
            - created_at: string (ISO timestamp)
            
            The ticket must also be written to CSV using write_csv_tool.
            """,
            agent=self.ticket_creator,
            context=[classify_task, analyze_task, feature_analyze_task],
            output_json=TicketOutput,
        )

        # Task 4: Quality review
        priority_rules_text = self._format_priority_rules()
        quality_task = Task(
            description=f"""
            Review the generated ticket for quality:
            - Title is descriptive and actionable
            - Priority matches severity/impact AND follows priority assignment rules below
            - Description is complete
            - Technical details present for bugs
            - Proper categorization
            - No critical information missing

            {priority_rules_text}
            If you need to read the tickets file for verification, use the read_csv_tool with this exact path: {self.tickets_file}

            Approve if quality standards are met, or request revisions with specific priority corrections.
            """,
            expected_output="""
            Quality assessment:
            - approved: boolean
            - feedback: string (if not approved, explain what needs revision)
            """,
            agent=self.quality_critic,
            context=[create_ticket_task],
        )

        return [
            classify_task,
            analyze_task,
            feature_analyze_task,
            create_ticket_task,
            quality_task,
        ]

    def _process_single_feedback_attempt(self, feedback: FeedbackInput) -> Dict[str, Any]:
        """Single attempt to process a feedback item (internal method).

        Args:
            feedback: FeedbackInput object to process.

        Returns:
            Dictionary with result status, ticket data, and any errors.

        Raises:
            Exception: If processing fails.
        """
        # Create tasks for this feedback
        tasks = self._create_tasks_for_feedback(feedback)

        # Create crew and execute
        crew = Crew(
            agents=[
                self.classifier,
                self.bug_analyzer,
                self.feature_extractor,
                self.ticket_creator,
                self.quality_critic,
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=self.verbose,
        )

        result = crew.kickoff()
        print(f"Processed feedback {feedback.source_id}")

        # Extract ticket from result for metrics tracking
        ticket_data = None

        # Try to extract ticket from tasks_output (ticket creation is task index 3)
        if hasattr(result, "tasks_output") and result.tasks_output and len(result.tasks_output) > 3:
            task_output = result.tasks_output[3]

            # Extract from TaskOutput object
            if hasattr(task_output, "raw") and task_output.raw:
                ticket_data = task_output.raw
            elif hasattr(task_output, "output") and task_output.output:
                ticket_data = task_output.output
            elif hasattr(task_output, "dict"):
                try:
                    ticket_data = task_output.dict()
                except Exception:
                    pass
            elif hasattr(task_output, "model_dump"):
                try:
                    ticket_data = task_output.model_dump()
                except Exception:
                    pass
            elif isinstance(task_output, TicketOutput):
                ticket_data = task_output.model_dump()
            elif isinstance(task_output, dict):
                ticket_data = task_output
            elif isinstance(task_output, str):
                try:
                    ticket_data = json.loads(task_output)
                except json.JSONDecodeError:
                    try:
                        ticket_data = ast.literal_eval(task_output)
                    except Exception:
                        pass

        # If not found, try result.json_dict
        if not ticket_data and hasattr(result, "json_dict") and result.json_dict:
            if isinstance(result.json_dict, dict):
                for value in result.json_dict.values():
                    if isinstance(value, dict) and ("ticket_id" in value or "title" in value):
                        ticket_data = value
                        break

        return {
            "status": "success",
            "source_id": feedback.source_id,
            "source_type": feedback.source_type,
            "ticket_data": ticket_data,
        }

    def _process_fallback(self, feedback: FeedbackInput, error_message: str) -> Dict[str, Any]:
        """Process feedback with fallback agent when main processing fails.

        Creates a minimal ticket with category "Failed" and a summary description.

        Args:
            feedback: FeedbackInput object that failed processing.
            error_message: Error message from the failed processing attempts.

        Returns:
            Dictionary with fallback ticket data.
        """
        print(f"Using fallback processing for {feedback.source_id}")

        try:
            # Create fallback task
            fallback_task = Task(
                description=f"""
                Create a minimal fallback ticket for the following feedback that failed normal processing.

                Original Feedback Text: {feedback.text}
                Source ID: {feedback.source_id}
                Source Type: {feedback.source_type}
                Error Reason: {error_message}

                Create a ticket with:
                - Category: "Failed" (this feedback could not be automatically classified)
                - Priority: "Medium" (default priority for manual review)
                - Title: Create a brief, descriptive title based on the feedback
                - Description: Summarize the original feedback in 2-3 sentences. Include note that this requires manual review.

                IMPORTANT: After creating the ticket, you MUST write it to the CSV file using the write_csv_tool.
                Use this EXACT file path: {self.tickets_file}
                Format: {{"records": [{{...ticket data...}}]}}
                Set append=True when writing.
                """,
                expected_output="""
                A JSON object with:
                - ticket_id: string (UUID)
                - source_id: string
                - source_type: string
                - title: string (brief descriptive title)
                - category: "Failed"
                - priority: "Medium"
                - description: string (2-3 sentence summary + note for manual review)
                - technical_details: string (error message from processing failure)
                - confidence: 0.0 (no confidence as this is a fallback)
                - status: "pending"
                - created_at: string (ISO timestamp)
                """,
                agent=self.fallback_agent,
                output_json=TicketOutput,
            )

            # Create minimal crew with just fallback agent
            crew = Crew(
                agents=[self.fallback_agent],
                tasks=[fallback_task],
                process=Process.sequential,
                verbose=self.verbose,
            )

            result = crew.kickoff()
            print(f"Fallback processing completed for {feedback.source_id}")

            # Create fallback ticket data
            fallback_ticket = {
                "ticket_id": str(uuid.uuid4()),
                "source_id": feedback.source_id,
                "source_type": feedback.source_type,
                "title": f"[Failed] Review needed: {feedback.text[:50]}...",
                "category": "Failed",
                "priority": "Medium",
                "description": (
                    f"This feedback could not be automatically processed and requires manual review. "
                    f"Original feedback: {feedback.text[:200]}..."
                ),
                "technical_details": f"Processing error: {error_message}",
                "confidence": 0.0,
                "status": "pending",
                "created_at": pd.Timestamp.now().isoformat(),
            }

            return {
                "status": "fallback",
                "source_id": feedback.source_id,
                "source_type": feedback.source_type,
                "ticket_data": fallback_ticket,
            }

        except Exception as e:
            print(f"Fallback processing also failed for {feedback.source_id}: {e}")
            # Create a minimal ticket directly without agent
            fallback_ticket = {
                "ticket_id": str(uuid.uuid4()),
                "source_id": feedback.source_id,
                "source_type": feedback.source_type,
                "title": f"[Failed] Manual review required: {feedback.source_id}",
                "category": "Failed",
                "priority": "Medium",
                "description": (
                    f"This feedback could not be processed automatically. "
                    f"Original text: {feedback.text[:300]}..."
                ),
                "technical_details": f"Processing error: {error_message}. Fallback error: {str(e)}",
                "confidence": 0.0,
                "status": "pending",
                "created_at": pd.Timestamp.now().isoformat(),
            }

            return {
                "status": "fallback",
                "source_id": feedback.source_id,
                "source_type": feedback.source_type,
                "ticket_data": fallback_ticket,
            }

    def _process_single_feedback(self, feedback: FeedbackInput) -> Dict[str, Any]:
        """Process a single feedback item with retry logic and fallback.

        Attempts to process the feedback up to max_retries times.
        If all retries fail, uses fallback processing to create a minimal ticket.

        Args:
            feedback: FeedbackInput object to process.

        Returns:
            Dictionary with result status, ticket data, and any errors.
        """
        last_error = None
        last_error_type = None

        # Retry loop
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"Processing {feedback.source_id} (attempt {attempt}/{self.max_retries})")
                result = self._process_single_feedback_attempt(feedback)
                return result

            except Exception as e:
                import traceback
                last_error = str(e)
                last_error_type = type(e).__name__
                print(f"Attempt {attempt}/{self.max_retries} failed for {feedback.source_id}: {last_error}")

                if attempt < self.max_retries:
                    print(f"Retrying {feedback.source_id}...")
                else:
                    print(traceback.format_exc())

        # All retries failed - use fallback processing
        print(f"All {self.max_retries} attempts failed for {feedback.source_id}. Using fallback processing.")
        fallback_result = self._process_fallback(feedback, last_error or "Unknown error")

        # Record the error for reporting
        fallback_result["retry_attempts"] = self.max_retries
        fallback_result["error_type"] = last_error_type
        fallback_result["error_message"] = last_error

        return fallback_result

    def kickoff(self, progress_callback=None) -> Dict[str, Any]:
        """Execute the feedback processing pipeline with parallel processing.

        Args:
            progress_callback: Optional callback function(progress, message) for progress updates.

        Returns:
            Dictionary with processing results and metrics.
        """
        print("Starting feedback processing pipeline")

        # Load feedback data
        feedback_items = self._load_feedback_data()
        print(f"Loaded {len(feedback_items)} feedback items")

        if not feedback_items:
            print("Warning: No feedback items to process")
            return {"status": "no_data", "processed": 0}

        # Process feedback items in parallel
        processed_count = 0
        tickets = []
        processing_errors = []
        total_items = len(feedback_items)
        completed_count = 0
        progress_lock = Lock()

        # Number of parallel workers (adjust based on API rate limits)
        max_workers = min(3, total_items)  # Max 3 parallel to avoid API rate limits

        print(f"Processing {total_items} items with {max_workers} parallel workers")

        if progress_callback:
            progress_callback(10, f"Starting parallel processing of {total_items} items...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_feedback = {
                executor.submit(self._process_single_feedback, feedback): feedback
                for feedback in feedback_items
            }

            # Process results as they complete
            for future in as_completed(future_to_feedback):
                feedback = future_to_feedback[future]

                with progress_lock:
                    completed_count += 1
                    progress = 10 + int((completed_count / total_items) * 80)
                    message = f"Completed {completed_count}/{total_items}: {feedback.source_id}"
                    print(message)

                    if progress_callback:
                        try:
                            progress_callback(progress, message)
                        except Exception as e:
                            print(f"Warning: Progress callback failed: {e}")

                try:
                    result = future.result()

                    # Handle both success and fallback statuses (both have ticket_data)
                    if result["status"] in ["success", "fallback"]:
                        ticket_data = result.get("ticket_data")

                        if ticket_data:
                            try:
                                if isinstance(ticket_data, TicketOutput):
                                    ticket_dict = ticket_data.model_dump()
                                elif isinstance(ticket_data, dict):
                                    ticket_dict = ticket_data
                                else:
                                    ticket_dict = None

                                if ticket_dict:
                                    if "ticket_id" not in ticket_dict:
                                        ticket_dict["ticket_id"] = str(uuid.uuid4())
                                    ticket_dict["source_id"] = result["source_id"]
                                    ticket_dict["source_type"] = result["source_type"]
                                    if "status" not in ticket_dict:
                                        ticket_dict["status"] = "pending"

                                    ticket = TicketOutput(**ticket_dict)
                                    with progress_lock:
                                        tickets.append(ticket.model_dump())
                                        processed_count += 1

                                        # Log fallback as a warning (not a full error)
                                        if result["status"] == "fallback":
                                            processing_errors.append({
                                                "source_id": result["source_id"],
                                                "source_type": result["source_type"],
                                                "error_type": f"Fallback_{result.get('error_type', 'Unknown')}",
                                                "error_message": f"Used fallback after {result.get('retry_attempts', 3)} retries: {result.get('error_message', 'Unknown')}",
                                                "timestamp": pd.Timestamp.now().isoformat(),
                                            })
                            except Exception as e:
                                print(f"Warning: Could not extract ticket for {result['source_id']}: {e}")
                                with progress_lock:
                                    processing_errors.append({
                                        "source_id": result["source_id"],
                                        "source_type": result["source_type"],
                                        "error_type": "TicketExtractionError",
                                        "error_message": str(e),
                                        "timestamp": pd.Timestamp.now().isoformat(),
                                    })
                        else:
                            with progress_lock:
                                processed_count += 1
                    else:
                        with progress_lock:
                            processing_errors.append({
                                "source_id": result["source_id"],
                                "source_type": result["source_type"],
                                "error_type": result.get("error_type", "Unknown"),
                                "error_message": result.get("error_message", "Unknown error"),
                                "timestamp": pd.Timestamp.now().isoformat(),
                            })

                except Exception as e:
                    print(f"Error getting result for {feedback.source_id}: {e}")
                    with progress_lock:
                        processing_errors.append({
                            "source_id": feedback.source_id,
                            "source_type": feedback.source_type,
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "timestamp": pd.Timestamp.now().isoformat(),
                        })

                # Write incremental metrics periodically
                with progress_lock:
                    if completed_count % 5 == 0 or completed_count == total_items:
                        try:
                            self._write_incremental_metrics(processed_count, len(processing_errors), total_items)
                        except Exception as me:
                            print(f"Warning: Could not write incremental metrics: {me}")

        # Tickets should be written by agents via write_csv_tool
        # If we extracted any tickets, write them as backup (agents may have already written them)
        if tickets:
            # Check if file exists and merge
            if self.tickets_file.exists():
                existing_df = pd.read_csv(self.tickets_file)
                # Ensure status column exists in existing data
                if "status" not in existing_df.columns:
                    existing_df["status"] = "pending"
                new_df = pd.DataFrame(tickets)
                # Ensure status column exists in new data
                if "status" not in new_df.columns:
                    new_df["status"] = "pending"
                # Avoid duplicates by ticket_id
                if not existing_df.empty and "ticket_id" in existing_df.columns:
                    existing_ids = set(existing_df["ticket_id"])
                    new_df = new_df[~new_df["ticket_id"].isin(existing_ids)]
                    if not new_df.empty:
                        df_tickets = pd.concat([existing_df, new_df], ignore_index=True)
                        df_tickets.to_csv(self.tickets_file, index=False)
                        print(f"Added {len(new_df)} new tickets to {self.tickets_file}")
                else:
                    df_tickets = pd.concat([existing_df, pd.DataFrame(tickets)], ignore_index=True)
                    df_tickets.to_csv(self.tickets_file, index=False)
                    print(f"Wrote {len(tickets)} tickets to {self.tickets_file}")
            else:
                df_tickets = pd.DataFrame(tickets)
                # Ensure status column exists
                if "status" not in df_tickets.columns:
                    df_tickets["status"] = "pending"
                df_tickets.to_csv(self.tickets_file, index=False)
                print(f"Wrote {len(tickets)} tickets to {self.tickets_file}")
        
        print(f"Processing complete: {processed_count} items processed")

        # Calculate metrics - read from file if in-memory extraction failed
        try:
            # Use tickets from file for accurate metrics if available
            tickets_for_metrics = tickets
            if not tickets_for_metrics and self.tickets_file.exists():
                print("Reading tickets from file for metrics calculation...")
                df_tickets = pd.read_csv(self.tickets_file)
                tickets_for_metrics = df_tickets.to_dict(orient="records")

            metrics = self._calculate_metrics(tickets_for_metrics)

            # Write metrics
            df_metrics = pd.DataFrame([metrics])
            if self.metrics_file.exists():
                df_existing = pd.read_csv(self.metrics_file)
                df_metrics = pd.concat([df_existing, df_metrics], ignore_index=True)
            df_metrics.to_csv(self.metrics_file, index=False)
            print(f"Wrote metrics to {self.metrics_file}")
        except Exception as e:
            print(f"Error writing metrics: {e}")
            import traceback
            print(traceback.format_exc())
            metrics = {"error": str(e)}

        # Write processing errors to CSV
        if processing_errors:
            try:
                df_errors = pd.DataFrame(processing_errors)
                if self.errors_file.exists():
                    df_existing = pd.read_csv(self.errors_file)
                    df_errors = pd.concat([df_existing, df_errors], ignore_index=True)
                df_errors.to_csv(self.errors_file, index=False)
                print(f"Wrote {len(processing_errors)} errors to {self.errors_file}")
            except Exception as e:
                print(f"Error writing processing errors: {e}")

        return {
            "status": "completed",
            "processed": processed_count,
            "failed": len(processing_errors),
            "tickets": len(tickets_for_metrics) if 'tickets_for_metrics' in dir() else len(tickets),
            "metrics": metrics,
        }

    def _calculate_metrics(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate processing metrics.

        Args:
            tickets: List of ticket dictionaries.

        Returns:
            Dictionary with metrics.
        """
        if not tickets:
            return {
                "run_id": str(uuid.uuid4()),
                "timestamp": pd.Timestamp.now().isoformat(),
                "total_processed": 0,
                "bugs_found": 0,
                "features_found": 0,
                "praise_found": 0,
                "complaints_found": 0,
                "spam_found": 0,
                "accuracy": 0.0,
                "avg_confidence": 0.0,
                "processing_time_sec": 0.0,
            }

        categories = [t.get("category", "") for t in tickets]
        confidences = [t.get("confidence", 0.0) for t in tickets if t.get("confidence")]

        return {
            "run_id": str(uuid.uuid4()),
            "timestamp": pd.Timestamp.now().isoformat(),
            "total_processed": len(tickets),
            "bugs_found": categories.count("Bug"),
            "features_found": categories.count("Feature Request"),
            "praise_found": categories.count("Praise"),
            "complaints_found": categories.count("Complaint"),
            "spam_found": categories.count("Spam"),
            "accuracy": 0.0,  # Will be calculated against expected_classifications.csv
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
            "processing_time_sec": 0.0,  # Would track actual time
        }

    _metrics_lock = Lock()  # Class-level lock for metrics writing

    def _write_incremental_metrics(self, processed: int, errors: int, total: int) -> None:
        """Write incremental progress metrics to file (thread-safe).

        Args:
            processed: Number of items successfully processed.
            errors: Number of items that failed.
            total: Total number of items to process.
        """
        with self._metrics_lock:
            # Read current tickets from file for accurate metrics
            tickets_for_metrics = []
            if self.tickets_file.exists():
                try:
                    df_tickets = pd.read_csv(self.tickets_file)
                    tickets_for_metrics = df_tickets.to_dict(orient="records")
                except Exception as e:
                    print(f"Warning: Could not read tickets for metrics: {e}")

            # Calculate metrics based on current tickets
            metrics = self._calculate_metrics(tickets_for_metrics)

            # Add progress info
            metrics["items_processed"] = processed
            metrics["items_failed"] = errors
            metrics["items_total"] = total
            metrics["progress_percent"] = round((processed + errors) / total * 100, 1) if total > 0 else 0

            # Write to metrics file (overwrite with latest)
            try:
                df_metrics = pd.DataFrame([metrics])
                self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
                df_metrics.to_csv(self.metrics_file, index=False)
                print(f"Updated metrics: {processed}/{total} processed, {errors} errors")
            except Exception as e:
                print(f"Error writing metrics file: {e}")
