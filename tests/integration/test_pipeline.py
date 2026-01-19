"""Integration tests for pipeline data flow."""

import pytest
from pathlib import Path

from crew import FeedbackCrew


@pytest.fixture
def test_data_dir(tmp_path):
    """Create test data directory with sample files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create sample reviews
    reviews = """review_id,platform,rating,review_text,user_name,date,app_version
REV001,App Store,1,App crashes on startup,TestUser1,2024-01-15,2.1.3
REV002,Google Play,5,Love this app!,TestUser2,2024-01-16,2.1.3
REV003,App Store,3,Please add dark mode,TestUser3,2024-01-17,2.1.3"""

    (data_dir / "app_store_reviews.csv").write_text(reviews)

    # Create sample emails
    emails = """email_id,subject,body,sender_email,timestamp,priority
EMAIL001,App Crash,My app keeps crashing,user@test.com,2024-01-15T10:00:00,High
EMAIL002,Feature Request,Can you add export?,user2@test.com,2024-01-16T11:00:00,"""

    (data_dir / "support_emails.csv").write_text(emails)

    return data_dir


@pytest.fixture
def output_dir(tmp_path):
    """Create output directory."""
    output = tmp_path / "output"
    output.mkdir()
    return output


class TestFullPipeline:
    """Test complete pipeline execution."""

    @pytest.mark.integration
    def test_crew_initialization(self, test_data_dir, output_dir):
        """Crew should initialize with correct directories."""
        crew = FeedbackCrew(
            data_dir=str(test_data_dir),
            output_dir=str(output_dir),
        )
        assert crew.data_dir == test_data_dir
        assert crew.output_dir == output_dir

    @pytest.mark.integration
    def test_loads_feedback_data(self, test_data_dir, output_dir):
        """Pipeline should load feedback from CSV files."""
        crew = FeedbackCrew(
            data_dir=str(test_data_dir),
            output_dir=str(output_dir),
        )
        feedback_items = crew._load_feedback_data()
        assert len(feedback_items) > 0
        assert all(item.source_id for item in feedback_items)

    @pytest.mark.integration
    def test_handles_empty_input(self, tmp_path):
        """Pipeline should handle empty input files gracefully."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Create empty CSV with headers only
        (data_dir / "app_store_reviews.csv").write_text(
            "review_id,platform,rating,review_text,user_name,date,app_version\n"
        )
        (data_dir / "support_emails.csv").write_text(
            "email_id,subject,body,sender_email,timestamp,priority\n"
        )

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        crew = FeedbackCrew(
            data_dir=str(data_dir),
            output_dir=str(output_dir),
        )
        # Should not raise exception
        feedback_items = crew._load_feedback_data()
        assert len(feedback_items) == 0

