"""Pydantic models for feedback input validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class FeedbackInput(BaseModel):
    """Normalized feedback input from CSV files."""

    source_id: str = Field(..., description="Unique identifier (review_id or email_id)")
    source_type: str = Field(
        ..., description="Source type: 'app_store_review' or 'email'"
    )
    text: str = Field(..., min_length=1, description="Feedback text content")
    subject: Optional[str] = Field(None, description="Email subject (for emails)")
    platform: Optional[str] = Field(None, description="Platform (App Store/Google Play)")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating 1-5 stars")
    app_version: Optional[str] = Field(None, description="App version")
    user_name: Optional[str] = Field(None, description="User name")
    date: Optional[str] = Field(None, description="Date string")
    sender_email: Optional[str] = Field(None, description="Sender email (for emails)")
    timestamp: Optional[str] = Field(None, description="Timestamp (for emails)")
    priority: Optional[str] = Field(None, description="User-indicated priority")

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        """Validate source type is one of allowed values."""
        allowed = {"app_store_review", "email"}
        if v not in allowed:
            raise ValueError(f"source_type must be one of {allowed}")
        return v

    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text is not empty or only whitespace."""
        if not v.strip():
            raise ValueError("text cannot be empty or whitespace only")
        return v.strip()

