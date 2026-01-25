"""Agent definitions for feedback processing pipeline."""

import logging
import os
from typing import List

from crewai import Agent
from langchain_openai import ChatOpenAI

from tools import read_csv_tool, write_csv_tool, log_processing_tool

logger = logging.getLogger(__name__)

# Validate and set OpenAI API key
def _validate_and_set_openai_api_key() -> None:
    """Validate and set OpenAI API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    
    # Check for common mistakes
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it in your .env file or environment."
        )
    
    # Check if the key starts with the variable name (common copy-paste error)
    if api_key.startswith("OPENAI_API_KEY="):
        raise ValueError(
            "OPENAI_API_KEY appears to include the variable name. "
            "The .env file should be: OPENAI_API_KEY=sk-... "
            "(not OPENAI_API_KEY=OPENAI_API_KEY=sk-...). "
            f"Found: {api_key[:50]}..."
        )
    
    # Validate key format (OpenAI keys start with sk-)
    if not api_key.startswith("sk-"):
        logger.warning(
            f"OpenAI API key doesn't start with 'sk-'. "
            f"Got: {api_key[:10]}... (first 10 chars). "
            "This might cause authentication errors."
        )
    
    # Ensure the environment variable is set correctly
    os.environ["OPENAI_API_KEY"] = api_key
    logger.info(f"OpenAI API key validated (starts with: {api_key[:7]}...)")

# Validate API key before initializing LLM
_validate_and_set_openai_api_key()

# Initialize LLM (ChatOpenAI reads OPENAI_API_KEY from environment automatically)
llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "gpt-4"),
    temperature=0.1,
)


def create_csv_reader_agent() -> Agent:
    """Create CSV Reader Agent for data ingestion.

    Returns:
        Configured CSV Reader Agent.
    """
    return Agent(
        role="Data Ingestion Specialist",
        goal="Read and parse feedback data from CSV files, normalizing different formats into a unified structure",
        backstory=(
            "You are an expert data engineer specializing in ETL pipelines. "
            "You ensure data quality and proper formatting before downstream processing. "
            "You handle missing fields gracefully and always maintain source tracking."
        ),
        tools=[read_csv_tool],
        verbose=True,
        max_iter=10,
        max_retry_limit=2,
        llm=llm,
    )


def create_classifier_agent() -> Agent:
    """Create Feedback Classifier Agent.

    Returns:
        Configured Feedback Classifier Agent.
    """
    return Agent(
        role="Senior Feedback Classification Specialist",
        goal=(
            "Accurately categorize user feedback into Bug, Feature Request, "
            "Praise, Complaint, or Spam with high confidence scores"
        ),
        backstory=(
            "You are an expert in natural language processing with years of experience "
            "analyzing customer feedback for SaaS products. You understand the nuances "
            "between a frustrated user reporting a bug versus requesting a feature. "
            "You never misclassify critical bugs as low-priority items. "
            "You provide clear reasoning for each classification decision."
        ),
        verbose=True,
        max_iter=15,
        max_retry_limit=2,
        llm=llm,
    )


def create_bug_analyzer_agent() -> Agent:
    """Create Bug Analyzer Agent.

    Returns:
        Configured Bug Analyzer Agent.
    """
    return Agent(
        role="Bug Analysis Specialist",
        goal=(
            "Extract technical details from bug reports including steps to reproduce, "
            "platform info, and severity assessment"
        ),
        backstory=(
            "You are a senior QA engineer with 10 years of experience triaging bug reports "
            "across mobile platforms. You are an expert at identifying critical bugs that "
            "need immediate attention. You always extract platform information and assess "
            "severity based on impact to user experience."
        ),
        verbose=True,
        max_iter=15,
        max_retry_limit=2,
        llm=llm,
    )


def create_feature_extractor_agent() -> Agent:
    """Create Feature Extractor Agent.

    Returns:
        Configured Feature Extractor Agent.
    """
    return Agent(
        role="Product Feature Analyst",
        goal=(
            "Identify feature requests, assess user impact, and estimate demand "
            "for product planning"
        ),
        backstory=(
            "You are a product manager with deep understanding of user needs. "
            "You are skilled at translating user wishes into actionable product requirements. "
            "You assess impact based on user language intensity and frequency of requests. "
            "You identify similar existing features to avoid duplication."
        ),
        verbose=True,
        max_iter=15,
        max_retry_limit=2,
        llm=llm,
    )


def create_ticket_creator_agent() -> Agent:
    """Create Ticket Creator Agent.

    Returns:
        Configured Ticket Creator Agent.
    """
    return Agent(
        role="Technical Ticket Specialist",
        goal=(
            "Generate structured, actionable tickets with consistent formatting "
            "and appropriate metadata"
        ),
        backstory=(
            "You are an engineering team lead experienced in creating clear, actionable "
            "tickets that developers can immediately work on. You ensure all tickets have "
            "proper titles, descriptions, priorities, and traceability to source feedback. "
            "You maintain consistent formatting across all tickets."
        ),
        tools=[write_csv_tool, log_processing_tool],
        verbose=True,
        max_iter=15,
        max_retry_limit=2,
        llm=llm,
    )


def create_quality_critic_agent() -> Agent:
    """Create Quality Critic Agent.

    Returns:
        Configured Quality Critic Agent.
    """
    return Agent(
        role="Quality Assurance Reviewer",
        goal=(
            "Review generated tickets for completeness, accuracy, and actionability "
            "before they reach the engineering team"
        ),
        backstory=(
            "You are a senior QA lead who ensures every ticket meets quality standards. "
            "You check that titles are descriptive, priorities match severity/impact, "
            "descriptions are complete, and technical details are present for bugs. "
            "You flag tickets that need revision and provide clear feedback."
        ),
        tools=[read_csv_tool],
        verbose=True,
        max_iter=15,
        max_retry_limit=2,
        llm=llm,
    )


def create_fallback_agent() -> Agent:
    """Create Fallback Agent for handling failed processing.

    This agent is used when normal processing fails after retries.
    It creates a minimal ticket with a summary of the original feedback.

    Returns:
        Configured Fallback Agent.
    """
    return Agent(
        role="Emergency Fallback Processor",
        goal=(
            "Create a minimal, valid ticket from feedback that failed normal processing. "
            "Summarize the feedback content and mark it for manual review."
        ),
        backstory=(
            "You are a reliable backup processor that ensures no feedback is lost. "
            "When the main processing pipeline fails, you step in to create a basic ticket "
            "with the essential information. You always produce valid output, even from "
            "difficult or malformed input. You focus on capturing the core message "
            "and flagging the item for manual review."
        ),
        tools=[write_csv_tool],
        verbose=True,
        max_iter=5,
        max_retry_limit=1,
        llm=llm,
    )

