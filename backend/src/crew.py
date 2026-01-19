"""Crew orchestration for feedback processing pipeline."""

import ast
import json
import os
import uuid
import warnings
from pathlib import Path
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
    ):
        """Initialize FeedbackCrew.

        Args:
            data_dir: Directory containing input CSV files.
            output_dir: Directory for output files.
            verbose: Enable verbose logging.
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose

        # Initialize agents
        self.csv_reader = create_csv_reader_agent()
        self.classifier = create_classifier_agent()
        self.bug_analyzer = create_bug_analyzer_agent()
        self.feature_extractor = create_feature_extractor_agent()
        self.ticket_creator = create_ticket_creator_agent()
        self.quality_critic = create_quality_critic_agent()

        # Output file paths
        self.tickets_file = self.output_dir / "generated_tickets.csv"
        self.log_file = self.output_dir / "processing_log.csv"
        self.metrics_file = self.output_dir / "metrics.csv"

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
            
            IMPORTANT: After creating the ticket, you MUST write it to the CSV file using the write_csv_tool.
            The file path is: {self.tickets_file}
            Format the ticket data as a JSON object with a "records" key containing a list with one ticket object.
            Set append=True when writing to add to existing tickets.
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
        quality_task = Task(
            description="""
            Review the generated ticket for quality:
            - Title is descriptive and actionable
            - Priority matches severity/impact
            - Description is complete
            - Technical details present for bugs
            - Proper categorization
            - No critical information missing
            
            Approve if quality standards are met, or request revisions.
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

    def kickoff(self) -> Dict[str, Any]:
        """Execute the feedback processing pipeline.

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

        # Process each feedback item
        processed_count = 0
        tickets = []

        for feedback in feedback_items:
            try:
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
                # The agent should write tickets to CSV using write_csv_tool
                # We extract here only for tracking/validation
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
                            # Try parsing Python dict string
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

                # Track ticket for metrics if extracted
                if ticket_data:
                    try:
                        if isinstance(ticket_data, TicketOutput):
                            ticket_dict = ticket_data.model_dump()
                        elif isinstance(ticket_data, dict):
                            ticket_dict = ticket_data
                        else:
                            continue
                        
                        # Ensure required fields
                        if "ticket_id" not in ticket_dict:
                            ticket_dict["ticket_id"] = str(uuid.uuid4())
                        ticket_dict["source_id"] = feedback.source_id
                        ticket_dict["source_type"] = feedback.source_type
                        # Ensure status field exists (default to pending)
                        if "status" not in ticket_dict:
                            ticket_dict["status"] = "pending"
                        
                        # Validate and track
                        ticket = TicketOutput(**ticket_dict)
                        tickets.append(ticket.model_dump())
                        processed_count += 1
                        print(f"Extracted ticket for {feedback.source_id}")
                    except Exception as e:
                        print(f"Warning: Could not extract ticket data for {feedback.source_id}: {e}")
                else:
                    # Agent should have written ticket via tool, so count as processed
                    processed_count += 1
                    print(f"Ticket should be written by agent for {feedback.source_id}")

            except Exception as e:
                import traceback
                print(f"Error processing feedback {feedback.source_id}: {e}")
                print(traceback.format_exc())

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

        # Calculate metrics
        metrics = self._calculate_metrics(tickets)

        # Write metrics
        df_metrics = pd.DataFrame([metrics])
        if self.metrics_file.exists():
            df_existing = pd.read_csv(self.metrics_file)
            df_metrics = pd.concat([df_existing, df_metrics], ignore_index=True)
        df_metrics.to_csv(self.metrics_file, index=False)

        return {
            "status": "completed",
            "processed": processed_count,
            "tickets": len(tickets),
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

