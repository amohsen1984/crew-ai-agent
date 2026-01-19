"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from models.feedback import FeedbackInput
from models.ticket import TicketOutput, ClassificationResult


class TestFeedbackInput:
    """Test FeedbackInput model validation."""

    def test_valid_app_store_review(self):
        """Valid app store review should parse correctly."""
        feedback = FeedbackInput(
            source_id="REV001",
            source_type="app_store_review",
            text="App crashes on startup",
            platform="App Store",
            rating=1,
            app_version="2.1.3",
        )
        assert feedback.source_id == "REV001"
        assert feedback.rating == 1

    def test_valid_email(self):
        """Valid support email should parse correctly."""
        feedback = FeedbackInput(
            source_id="EMAIL001",
            source_type="email",
            text="Need help with login",
            subject="Login Issue",
        )
        assert feedback.source_type == "email"

    def test_invalid_source_type_raises(self):
        """Invalid source type should raise ValidationError."""
        with pytest.raises(ValidationError):
            FeedbackInput(
                source_id="X001",
                source_type="invalid_type",
                text="Some text",
            )

    def test_empty_text_raises(self):
        """Empty text should raise ValidationError."""
        with pytest.raises(ValidationError):
            FeedbackInput(
                source_id="REV001",
                source_type="app_store_review",
                text="",
            )


class TestTicketOutput:
    """Test TicketOutput model validation."""

    def test_valid_ticket(self):
        """Valid ticket should pass validation."""
        ticket = TicketOutput(
            ticket_id="TKT-001",
            source_id="REV001",
            source_type="app_store_review",
            title="[Bug] App crashes on startup",
            category="Bug",
            priority="High",
            description="User reports crash on app launch",
            confidence=0.92,
        )
        assert ticket.category == "Bug"

    def test_invalid_category_raises(self):
        """Invalid category should raise ValidationError."""
        with pytest.raises(ValidationError):
            TicketOutput(
                ticket_id="TKT-001",
                source_id="REV001",
                source_type="app_store_review",
                title="Test",
                category="InvalidCategory",
                priority="High",
                description="Test",
                confidence=0.9,
            )

    def test_invalid_priority_raises(self):
        """Invalid priority should raise ValidationError."""
        with pytest.raises(ValidationError):
            TicketOutput(
                ticket_id="TKT-001",
                source_id="REV001",
                source_type="app_store_review",
                title="Test",
                category="Bug",
                priority="Urgent",  # Invalid
                description="Test",
                confidence=0.9,
            )

    def test_confidence_out_of_range_raises(self):
        """Confidence outside 0-1 should raise ValidationError."""
        with pytest.raises(ValidationError):
            TicketOutput(
                ticket_id="TKT-001",
                source_id="REV001",
                source_type="app_store_review",
                title="Test",
                category="Bug",
                priority="High",
                description="Test",
                confidence=1.5,  # Invalid
            )


class TestClassificationResult:
    """Test ClassificationResult model validation."""

    def test_valid_classification(self):
        """Valid classification should pass validation."""
        result = ClassificationResult(
            category="Bug",
            confidence=0.85,
            reasoning="Contains crash-related keywords",
        )
        assert result.category == "Bug"
        assert result.confidence == 0.85

    def test_invalid_category_raises(self):
        """Invalid category should raise ValidationError."""
        with pytest.raises(ValidationError):
            ClassificationResult(
                category="Invalid",
                confidence=0.8,
                reasoning="Test",
            )

