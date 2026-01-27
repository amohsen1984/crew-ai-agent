"""Pydantic models for ticket output validation."""

import uuid
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class ClassificationResult(BaseModel):
    """Classification result from Feedback Classifier Agent."""

    category: str = Field(
        ...,
        description="Category: Bug, Feature Request, Praise, Complaint, or Spam",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0"
    )
    reasoning: str = Field(..., min_length=10, description="Explanation for classification")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category is one of allowed values."""
        allowed = {"Bug", "Feature Request", "Praise", "Complaint", "Spam"}
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return v


class BugAnalysis(BaseModel):
    """Bug analysis result from Bug Analyzer Agent."""

    steps_to_reproduce: Optional[str] = Field(
        None, description="Steps to reproduce the bug"
    )
    platform: Optional[str] = Field(None, description="Platform/OS version")
    app_version: Optional[str] = Field(None, description="App version")
    device_model: Optional[str] = Field(None, description="Device model if mentioned")
    severity: str = Field(
        ..., description="Severity: Critical, High, Medium, or Low"
    )
    affected_functionality: Optional[str] = Field(
        None, description="Affected functionality description"
    )

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity is one of allowed values."""
        allowed = {"Critical", "High", "Medium", "Low"}
        if v not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return v


class FeatureAnalysis(BaseModel):
    """Feature analysis result from Feature Extractor Agent."""

    feature_summary: str = Field(..., min_length=10, description="Feature request summary")
    user_pain_point: Optional[str] = Field(
        None, description="User pain point or motivation"
    )
    impact: str = Field(..., description="Impact: High, Medium, or Low")
    similar_features: Optional[str] = Field(
        None, description="Similar existing features if any"
    )
    implementation_complexity: Optional[str] = Field(
        None, description="Estimated complexity"
    )

    @field_validator("impact")
    @classmethod
    def validate_impact(cls, v: str) -> str:
        """Validate impact is one of allowed values."""
        allowed = {"High", "Medium", "Low"}
        if v not in allowed:
            raise ValueError(f"impact must be one of {allowed}")
        return v


class TicketOutput(BaseModel):
    """Structured ticket output."""

    ticket_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ticket identifier (UUID) - auto-generated if not provided"
    )
    source_id: str = Field(..., description="Original feedback ID")
    source_type: str = Field(
        ..., description="Source type: 'app_store_review' or 'email'"
    )
    title: str = Field(..., min_length=5, max_length=200, description="Ticket title")
    category: str = Field(
        ...,
        description="Category: Bug, Feature Request, Praise, Complaint, Spam, or Failed",
    )
    priority: str = Field(
        ..., description="Priority: Critical, High, Medium, or Low"
    )
    description: str = Field(..., min_length=10, description="Full ticket description")
    technical_details: Optional[str] = Field(
        None, description="Technical details (for bugs only)"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Classification confidence score"
    )
    status: str = Field(
        default="pending",
        description="Ticket status: pending, approved, rejected"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Creation timestamp",
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category is one of allowed values."""
        allowed = {"Bug", "Feature Request", "Praise", "Complaint", "Spam", "Failed"}
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority is one of allowed values."""
        allowed = {"Critical", "High", "Medium", "Low"}
        if v not in allowed:
            raise ValueError(f"priority must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of allowed values."""
        allowed = {"pending", "approved", "rejected"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v.lower()

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        """Ensure title is not empty or only whitespace."""
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace only")
        return v.strip()

