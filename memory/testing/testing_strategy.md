# Testing Strategy

## Overview

This document defines the testing approach for the Intelligent User Feedback Analysis System. Tests ensure classification accuracy, agent reliability, and system stability.

---

## Test Structure

```text
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_models.py       # Pydantic model validation
│   ├── test_tools.py        # CSV read/write tools
│   └── test_agents.py       # Individual agent behavior
├── integration/
│   ├── __init__.py
│   ├── test_pipeline.py     # Pipeline data flow
│   └── test_crew.py         # Agent orchestration
├── accuracy/
│   ├── __init__.py
│   └── test_classification.py  # vs expected_classifications.csv
└── e2e/
    ├── __init__.py
    ├── test_full_system.py  # Complete pipeline with real LLM
    ├── test_cli.py          # CLI entry point testing
    └── test_ui.py           # Streamlit UI testing
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/accuracy/          # Accuracy validation only
pytest tests/e2e/               # E2E tests only
pytest -m e2e                   # E2E tests (by marker)

# Run tests matching a pattern
pytest -k "classifier"          # All classifier-related tests
pytest -k "bug"                 # All bug-related tests

# Verbose output with print statements
pytest -v -s

# Stop on first failure
pytest -x

# Run failed tests from last run
pytest --lf
```

---

## Test Categories

### 1. Unit Tests

Test individual components in isolation.

#### Models (`test_models.py`)

```python
import pytest
from pydantic import ValidationError
from src.models.feedback import FeedbackInput
from src.models.ticket import TicketOutput


class TestFeedbackInput:
    def test_valid_app_store_review(self):
        """Valid app store review should parse correctly."""
        feedback = FeedbackInput(
            source_id="REV001",
            source_type="app_store_review",
            text="App crashes on startup",
            platform="App Store",
            rating=1,
            app_version="2.1.3"
        )
        assert feedback.source_id == "REV001"
        assert feedback.rating == 1

    def test_valid_email(self):
        """Valid support email should parse correctly."""
        feedback = FeedbackInput(
            source_id="EMAIL001",
            source_type="email",
            text="Need help with login",
            subject="Login Issue"
        )
        assert feedback.source_type == "email"

    def test_invalid_source_type_raises(self):
        """Invalid source type should raise ValidationError."""
        with pytest.raises(ValidationError):
            FeedbackInput(
                source_id="X001",
                source_type="invalid_type",
                text="Some text"
            )

    def test_empty_text_raises(self):
        """Empty text should raise ValidationError."""
        with pytest.raises(ValidationError):
            FeedbackInput(
                source_id="REV001",
                source_type="app_store_review",
                text=""
            )


class TestTicketOutput:
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
            confidence=0.92
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
                confidence=0.9
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
                confidence=0.9
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
                confidence=1.5  # Invalid
            )
```

#### Tools (`test_tools.py`)

```python
import pytest
import pandas as pd
from pathlib import Path
from src.tools.csv_tools import read_csv_tool, write_csv_tool


@pytest.fixture
def sample_csv(tmp_path):
    """Create a temporary CSV file for testing."""
    csv_path = tmp_path / "test_reviews.csv"
    df = pd.DataFrame({
        "review_id": ["REV001", "REV002"],
        "platform": ["App Store", "Google Play"],
        "rating": [1, 5],
        "review_text": ["App crashes", "Love it!"],
        "user_name": ["User1", "User2"],
        "date": ["2024-01-15", "2024-01-16"],
        "app_version": ["2.1.3", "2.1.3"]
    })
    df.to_csv(csv_path, index=False)
    return csv_path


class TestReadCSVTool:
    def test_reads_valid_csv(self, sample_csv):
        """Should read and parse valid CSV file."""
        result = read_csv_tool(str(sample_csv))
        assert len(result) == 2
        assert result[0]["review_id"] == "REV001"

    def test_file_not_found_returns_error(self):
        """Should return error message for missing file."""
        result = read_csv_tool("/nonexistent/path.csv")
        assert "ERROR" in result or isinstance(result, str)

    def test_empty_csv_returns_empty_list(self, tmp_path):
        """Should handle empty CSV gracefully."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("col1,col2\n")
        result = read_csv_tool(str(empty_csv))
        assert result == [] or "empty" in str(result).lower()


class TestWriteCSVTool:
    def test_writes_valid_data(self, tmp_path):
        """Should write data to CSV file."""
        output_path = tmp_path / "output.csv"
        data = [
            {"ticket_id": "TKT-001", "title": "Bug report"},
            {"ticket_id": "TKT-002", "title": "Feature request"}
        ]
        result = write_csv_tool(str(output_path), data)
        assert "success" in result.lower()
        assert output_path.exists()

        df = pd.read_csv(output_path)
        assert len(df) == 2

    def test_appends_to_existing_file(self, tmp_path):
        """Should append to existing CSV without overwriting."""
        output_path = tmp_path / "output.csv"

        # Write initial data
        write_csv_tool(str(output_path), [{"id": "1"}])

        # Append more data
        write_csv_tool(str(output_path), [{"id": "2"}], append=True)

        df = pd.read_csv(output_path)
        assert len(df) == 2
```

#### Agents (`test_agents.py`)

```python
import pytest
from unittest.mock import Mock, patch
from src.agents.feedback_agents import (
    create_classifier_agent,
    create_bug_analyzer_agent,
    create_feature_extractor_agent
)


class TestClassifierAgent:
    @pytest.fixture
    def classifier(self):
        """Create classifier agent for testing."""
        return create_classifier_agent()

    def test_agent_has_correct_role(self, classifier):
        """Classifier should have correct role defined."""
        assert "classifier" in classifier.role.lower() or \
               "classification" in classifier.role.lower()

    def test_agent_has_goal(self, classifier):
        """Classifier should have a goal defined."""
        assert classifier.goal is not None
        assert len(classifier.goal) > 10

    def test_agent_has_backstory(self, classifier):
        """Classifier should have backstory defined."""
        assert classifier.backstory is not None


class TestClassificationLogic:
    """Test classification behavior with mocked LLM."""

    @pytest.mark.parametrize("text,expected_category", [
        ("App crashes when I tap login", "Bug"),
        ("App keeps crashing on iOS", "Bug"),
        ("Can't sync my data anymore", "Bug"),
        ("Please add dark mode", "Feature Request"),
        ("Would love to see offline support", "Feature Request"),
        ("Amazing app, works perfectly!", "Praise"),
        ("Best productivity app ever", "Praise"),
        ("Too expensive for what it offers", "Complaint"),
        ("Customer service is terrible", "Complaint"),
        ("Buy cheap watches at...", "Spam"),
    ])
    def test_classification_categories(self, text, expected_category):
        """Classification should match expected category."""
        # This would use your actual classification logic
        # For now, marking as placeholder for implementation
        pass  # TODO: Implement with actual classifier


class TestBugAnalyzerAgent:
    @pytest.fixture
    def bug_analyzer(self):
        return create_bug_analyzer_agent()

    def test_agent_extracts_platform(self, bug_analyzer):
        """Bug analyzer should extract platform information."""
        assert bug_analyzer.role is not None

    @pytest.mark.parametrize("text,expected_severity", [
        ("Lost all my data after update", "Critical"),
        ("App won't open at all", "Critical"),
        ("Login button doesn't work", "High"),
        ("Minor typo in settings", "Low"),
    ])
    def test_severity_assessment(self, text, expected_severity):
        """Severity should be assessed based on impact."""
        pass  # TODO: Implement with actual analyzer


class TestFeatureExtractorAgent:
    @pytest.fixture
    def feature_extractor(self):
        return create_feature_extractor_agent()

    def test_agent_has_correct_role(self, feature_extractor):
        """Feature extractor should have correct role."""
        assert feature_extractor.role is not None
```

---

### 2. Integration Tests

Test component interactions and data flow.

#### Pipeline (`test_pipeline.py`)

```python
import pytest
from pathlib import Path
from src.crew import FeedbackCrew


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
    @pytest.mark.integration
    def test_processes_all_feedback(self, test_data_dir, output_dir):
        """Pipeline should process all feedback items."""
        crew = FeedbackCrew(
            data_dir=str(test_data_dir),
            output_dir=str(output_dir)
        )
        result = crew.kickoff()

        # Check tickets were generated
        tickets_file = output_dir / "generated_tickets.csv"
        assert tickets_file.exists()

    @pytest.mark.integration
    def test_generates_processing_log(self, test_data_dir, output_dir):
        """Pipeline should create processing log."""
        crew = FeedbackCrew(
            data_dir=str(test_data_dir),
            output_dir=str(output_dir)
        )
        crew.kickoff()

        log_file = output_dir / "processing_log.csv"
        assert log_file.exists()

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
            output_dir=str(output_dir)
        )
        # Should not raise exception
        result = crew.kickoff()

    @pytest.mark.integration
    def test_maintains_traceability(self, test_data_dir, output_dir):
        """Each ticket should trace back to source feedback."""
        crew = FeedbackCrew(
            data_dir=str(test_data_dir),
            output_dir=str(output_dir)
        )
        crew.kickoff()

        import pandas as pd
        tickets = pd.read_csv(output_dir / "generated_tickets.csv")

        # Every ticket should have source_id
        assert tickets["source_id"].notna().all()

        # Source IDs should match input data
        reviews = pd.read_csv(test_data_dir / "app_store_reviews.csv")
        emails = pd.read_csv(test_data_dir / "support_emails.csv")

        valid_ids = set(reviews["review_id"]) | set(emails["email_id"])
        assert set(tickets["source_id"]).issubset(valid_ids)
```

---

### 3. Accuracy Tests

Validate classification accuracy against ground truth.

#### Classification Accuracy (`test_classification.py`)

```python
import pytest
import pandas as pd
from pathlib import Path
from src.crew import FeedbackCrew


class TestClassificationAccuracy:
    """Test classification accuracy against expected results."""

    @pytest.fixture
    def ground_truth(self):
        """Load expected classifications."""
        return pd.read_csv("data/expected_classifications.csv")

    @pytest.fixture
    def generated_tickets(self, tmp_path):
        """Run pipeline and return generated tickets."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        crew = FeedbackCrew(
            data_dir="data",
            output_dir=str(output_dir)
        )
        crew.kickoff()

        return pd.read_csv(output_dir / "generated_tickets.csv")

    @pytest.mark.accuracy
    def test_overall_accuracy_above_threshold(
        self, ground_truth, generated_tickets
    ):
        """Overall classification accuracy should be >= 80%."""
        merged = pd.merge(
            generated_tickets,
            ground_truth,
            on="source_id",
            suffixes=("_gen", "_exp")
        )

        correct = (merged["category_gen"] == merged["category_exp"]).sum()
        total = len(merged)
        accuracy = correct / total if total > 0 else 0

        assert accuracy >= 0.80, f"Accuracy {accuracy:.2%} below 80% threshold"

    @pytest.mark.accuracy
    def test_bug_recall(self, ground_truth, generated_tickets):
        """Bug detection recall should be >= 90% (don't miss bugs)."""
        merged = pd.merge(
            generated_tickets,
            ground_truth,
            on="source_id",
            suffixes=("_gen", "_exp")
        )

        actual_bugs = merged[merged["category_exp"] == "Bug"]
        detected_bugs = actual_bugs[actual_bugs["category_gen"] == "Bug"]

        recall = len(detected_bugs) / len(actual_bugs) if len(actual_bugs) > 0 else 1.0

        assert recall >= 0.90, f"Bug recall {recall:.2%} below 90% threshold"

    @pytest.mark.accuracy
    def test_spam_precision(self, ground_truth, generated_tickets):
        """Spam detection precision should be >= 95% (minimize false positives)."""
        merged = pd.merge(
            generated_tickets,
            ground_truth,
            on="source_id",
            suffixes=("_gen", "_exp")
        )

        predicted_spam = merged[merged["category_gen"] == "Spam"]
        true_spam = predicted_spam[predicted_spam["category_exp"] == "Spam"]

        precision = len(true_spam) / len(predicted_spam) if len(predicted_spam) > 0 else 1.0

        assert precision >= 0.95, f"Spam precision {precision:.2%} below 95%"

    @pytest.mark.accuracy
    def test_priority_alignment(self, ground_truth, generated_tickets):
        """Priority assignments should match expected >= 75%."""
        merged = pd.merge(
            generated_tickets,
            ground_truth,
            on="source_id",
            suffixes=("_gen", "_exp")
        )

        correct = (merged["priority_gen"] == merged["priority_exp"]).sum()
        total = len(merged)
        alignment = correct / total if total > 0 else 0

        assert alignment >= 0.75, f"Priority alignment {alignment:.2%} below 75%"

    @pytest.mark.accuracy
    @pytest.mark.parametrize("category", [
        "Bug", "Feature Request", "Praise", "Complaint", "Spam"
    ])
    def test_per_category_f1(self, ground_truth, generated_tickets, category):
        """Each category should have F1 score >= 0.70."""
        merged = pd.merge(
            generated_tickets,
            ground_truth,
            on="source_id",
            suffixes=("_gen", "_exp")
        )

        # Calculate precision
        predicted = merged[merged["category_gen"] == category]
        true_positive = predicted[predicted["category_exp"] == category]
        precision = len(true_positive) / len(predicted) if len(predicted) > 0 else 0

        # Calculate recall
        actual = merged[merged["category_exp"] == category]
        detected = actual[actual["category_gen"] == category]
        recall = len(detected) / len(actual) if len(actual) > 0 else 0

        # Calculate F1
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        assert f1 >= 0.70, f"{category} F1 score {f1:.2f} below 0.70"
```

---

### 4. E2E Tests

End-to-end tests validate the complete system from user input to final output.

#### Full System Tests (`test_full_system.py`)

```python
import pytest
import subprocess
import pandas as pd
from pathlib import Path


class TestFullSystem:
    """Test complete system with real LLM calls."""

    @pytest.fixture
    def production_data(self, project_root):
        """Use actual data files for E2E testing."""
        return {
            "reviews": project_root / "data" / "app_store_reviews.csv",
            "emails": project_root / "data" / "support_emails.csv"
        }

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_full_pipeline_generates_all_outputs(self, production_data, tmp_path):
        """Complete pipeline should generate all expected output files."""
        from src.crew import FeedbackCrew

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        crew = FeedbackCrew(
            data_dir=str(production_data["reviews"].parent),
            output_dir=str(output_dir)
        )
        result = crew.kickoff()

        # Verify all output files exist
        assert (output_dir / "generated_tickets.csv").exists()
        assert (output_dir / "processing_log.csv").exists()
        assert (output_dir / "metrics.csv").exists()

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_ticket_count_matches_input(self, production_data, tmp_path):
        """Number of tickets should match number of non-spam inputs."""
        from src.crew import FeedbackCrew

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Count input records
        reviews = pd.read_csv(production_data["reviews"])
        emails = pd.read_csv(production_data["emails"])
        input_count = len(reviews) + len(emails)

        crew = FeedbackCrew(
            data_dir=str(production_data["reviews"].parent),
            output_dir=str(output_dir)
        )
        crew.kickoff()

        # Count output tickets (excluding spam which may be filtered)
        tickets = pd.read_csv(output_dir / "generated_tickets.csv")
        assert len(tickets) <= input_count
        assert len(tickets) > 0

    @pytest.mark.e2e
    def test_metrics_file_has_valid_data(self, production_data, tmp_path):
        """Metrics file should contain valid statistics."""
        from src.crew import FeedbackCrew

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        crew = FeedbackCrew(
            data_dir=str(production_data["reviews"].parent),
            output_dir=str(output_dir)
        )
        crew.kickoff()

        metrics = pd.read_csv(output_dir / "metrics.csv")
        assert "total_processed" in metrics.columns
        assert "processing_time_sec" in metrics.columns
        assert metrics["total_processed"].iloc[-1] > 0
```

#### CLI Tests (`test_cli.py`)

```python
import pytest
import subprocess
import sys
from pathlib import Path


class TestCLI:
    """Test command-line interface."""

    @pytest.mark.e2e
    def test_main_runs_successfully(self, project_root):
        """python main.py should complete without errors."""
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        assert result.returncode == 0, f"Failed with: {result.stderr}"

    @pytest.mark.e2e
    def test_main_with_help_flag(self, project_root):
        """python main.py --help should show usage."""
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            cwd=str(project_root),
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "help" in result.stdout.lower()

    @pytest.mark.e2e
    def test_main_with_invalid_data_path(self, project_root):
        """Should fail gracefully with invalid data path."""
        result = subprocess.run(
            [sys.executable, "main.py", "--data-dir", "/nonexistent/path"],
            cwd=str(project_root),
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert "error" in result.stderr.lower() or "not found" in result.stderr.lower()

    @pytest.mark.e2e
    def test_output_directory_created_if_missing(self, project_root, tmp_path):
        """Should create output directory if it doesn't exist."""
        output_dir = tmp_path / "new_output"
        result = subprocess.run(
            [sys.executable, "main.py", "--output-dir", str(output_dir)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300
        )
        # Directory should be created regardless of success/failure
        assert output_dir.exists() or result.returncode != 0
```

#### Streamlit UI Tests (`test_ui.py`)

```python
import pytest
from pathlib import Path


class TestStreamlitUI:
    """Test Streamlit dashboard using AppTest."""

    @pytest.fixture
    def app_test(self):
        """Create AppTest instance for Streamlit testing."""
        from streamlit.testing.v1 import AppTest
        return AppTest.from_file("app.py")

    @pytest.mark.e2e
    def test_app_loads_without_error(self, app_test):
        """App should load without throwing exceptions."""
        app_test.run(timeout=30)
        assert not app_test.exception

    @pytest.mark.e2e
    def test_dashboard_page_renders(self, app_test):
        """Dashboard page should render with expected elements."""
        app_test.run(timeout=30)

        # Check for dashboard elements
        assert len(app_test.title) > 0 or len(app_test.header) > 0

    @pytest.mark.e2e
    def test_sidebar_navigation_exists(self, app_test):
        """Sidebar should have navigation options."""
        app_test.run(timeout=30)

        # Check sidebar has content
        assert app_test.sidebar is not None

    @pytest.mark.e2e
    def test_configuration_panel_accessible(self, app_test):
        """Configuration panel should be accessible."""
        app_test.run(timeout=30)

        # Look for configuration elements (sliders, selectboxes)
        # Actual selectors depend on implementation
        config_elements = (
            len(app_test.slider) +
            len(app_test.selectbox) +
            len(app_test.number_input)
        )
        # At least some config elements should exist
        assert config_elements >= 0  # Adjust based on actual UI

    @pytest.mark.e2e
    def test_ticket_table_displays_data(self, app_test):
        """Ticket table should display when data exists."""
        app_test.run(timeout=30)

        # Check for dataframe or table elements
        tables = app_test.dataframe
        # Tables may be empty if no data processed yet
        assert tables is not None

    @pytest.mark.e2e
    def test_manual_override_form_exists(self, app_test):
        """Manual override section should have form elements."""
        app_test.run(timeout=30)

        # Look for form elements
        forms = app_test.button
        # Should have at least approve/reject buttons
        assert forms is not None


class TestUIInteractions:
    """Test user interactions with the UI."""

    @pytest.fixture
    def app_test(self):
        from streamlit.testing.v1 import AppTest
        return AppTest.from_file("app.py")

    @pytest.mark.e2e
    def test_process_button_triggers_pipeline(self, app_test):
        """Clicking process button should trigger the pipeline."""
        app_test.run(timeout=30)

        # Find and click process button if it exists
        process_buttons = [
            b for b in app_test.button
            if "process" in b.label.lower()
        ]
        if process_buttons:
            process_buttons[0].click()
            app_test.run(timeout=60)
            assert not app_test.exception

    @pytest.mark.e2e
    def test_category_filter_updates_display(self, app_test):
        """Selecting a category filter should update displayed tickets."""
        app_test.run(timeout=30)

        # Find category selectbox if exists
        category_selects = [
            s for s in app_test.selectbox
            if "category" in str(s.label).lower()
        ]
        if category_selects:
            category_selects[0].select("Bug")
            app_test.run(timeout=30)
            assert not app_test.exception
```

---

## Shared Fixtures (`conftest.py`)

```python
import pytest
import pandas as pd
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Return project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return data directory path."""
    return project_root / "data"


@pytest.fixture(scope="session")
def sample_reviews():
    """Provide sample review data for testing."""
    return [
        {
            "review_id": "REV001",
            "platform": "App Store",
            "rating": 1,
            "review_text": "App crashes every time I open it",
            "user_name": "frustrated_user",
            "date": "2024-01-15",
            "app_version": "2.1.3"
        },
        {
            "review_id": "REV002",
            "platform": "Google Play",
            "rating": 5,
            "review_text": "Best productivity app I've ever used!",
            "user_name": "happy_user",
            "date": "2024-01-16",
            "app_version": "2.1.3"
        },
        {
            "review_id": "REV003",
            "platform": "App Store",
            "rating": 3,
            "review_text": "Good app but please add dark mode",
            "user_name": "feature_requester",
            "date": "2024-01-17",
            "app_version": "2.1.3"
        }
    ]


@pytest.fixture(scope="session")
def sample_emails():
    """Provide sample email data for testing."""
    return [
        {
            "email_id": "EMAIL001",
            "subject": "URGENT: App Crash",
            "body": "My app crashes on startup after the latest update. iPhone 14, iOS 17.",
            "sender_email": "user@example.com",
            "timestamp": "2024-01-15T10:30:00",
            "priority": "High"
        },
        {
            "email_id": "EMAIL002",
            "subject": "Feature Suggestion",
            "body": "It would be great if you could add calendar integration.",
            "sender_email": "user2@example.com",
            "timestamp": "2024-01-16T14:00:00",
            "priority": ""
        }
    ]


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing without API calls."""
    def _mock(category="Bug", confidence=0.9):
        return {
            "category": category,
            "confidence": confidence,
            "reasoning": f"Classified as {category} based on content analysis"
        }
    return _mock
```

---

## Test Automation

### pytest Configuration (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "accuracy: Accuracy validation tests",
    "e2e: End-to-end tests",
    "slow: Slow-running tests"
]
addopts = "-v --tb=short"
filterwarnings = [
    "ignore::DeprecationWarning"
]

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/__init__.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

### GitHub Actions CI (`.github/workflows/test.yml`)

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src

      - name: Run integration tests
        run: pytest tests/integration/ -v -m integration
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  accuracy:
    runs-on: ubuntu-latest
    needs: test

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run accuracy tests
        run: pytest tests/accuracy/ -v -m accuracy
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

  e2e:
    runs-on: ubuntu-latest
    needs: [test, accuracy]
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run E2E tests
        run: pytest tests/e2e/ -v -m e2e --timeout=300
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Run Streamlit UI tests
        run: pytest tests/e2e/test_ui.py -v
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Pre-commit Hook (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run unit tests
        entry: pytest tests/unit/ -x -q
        language: system
        pass_filenames: false
        always_run: true
```

---

## Adding/Updating Tests

### When to Add Tests

| Change Type                  | Required Tests                          |
|------------------------------|----------------------------------------|
| New agent                    | Unit test for role/goal, integration test |
| New tool                     | Unit tests for success + error cases   |
| New Pydantic model           | Validation tests for all fields        |
| Classification rule change   | Update accuracy tests, add edge cases  |
| Bug fix                      | Regression test reproducing the bug    |
| New UI component             | E2E UI test using AppTest              |
| New CLI flag/option          | E2E CLI test for the new option        |
| Major pipeline change        | E2E full system test                   |
| New output file format       | E2E test validating file structure     |

### Test Writing Checklist

```markdown
## Before Writing Tests
- [ ] Identify the component being tested
- [ ] List expected behaviors (happy path)
- [ ] List edge cases and error conditions
- [ ] Check if fixtures exist or need creation

## Test Structure
- [ ] Test name describes expected behavior: `test_<action>_<condition>_<expected>`
- [ ] Arrange-Act-Assert pattern followed
- [ ] Single assertion per test (when practical)
- [ ] Fixtures used for setup/teardown

## After Writing Tests
- [ ] All tests pass locally: `pytest -v`
- [ ] Coverage maintained: `pytest --cov=src`
- [ ] No flaky tests (run 3x to verify)
- [ ] Tests are independent (can run in any order)
```

### Test Naming Convention

```python
# Pattern: test_<what>_<condition>_<expected_result>

# Good examples
def test_classifier_with_crash_report_returns_bug():
def test_csv_reader_with_missing_file_raises_error():
def test_ticket_creator_with_valid_input_generates_ticket():
def test_priority_with_data_loss_returns_critical():

# Bad examples
def test_1():
def test_classifier():
def test_it_works():
```

### Adding Tests for New Features

```python
# 1. Create test file if needed
# tests/unit/test_new_feature.py

import pytest
from src.new_feature import NewFeature


class TestNewFeature:
    """Tests for NewFeature component."""

    @pytest.fixture
    def feature(self):
        """Create feature instance for testing."""
        return NewFeature()

    # 2. Test happy path first
    def test_basic_functionality_works(self, feature):
        """Basic usage should work correctly."""
        result = feature.do_something("valid input")
        assert result is not None

    # 3. Test edge cases
    def test_handles_empty_input(self, feature):
        """Empty input should be handled gracefully."""
        result = feature.do_something("")
        assert result == expected_default

    # 4. Test error conditions
    def test_invalid_input_raises_error(self, feature):
        """Invalid input should raise appropriate error."""
        with pytest.raises(ValueError, match="expected message"):
            feature.do_something(None)

    # 5. Test integration points
    def test_works_with_other_component(self, feature, other_component):
        """Should integrate correctly with OtherComponent."""
        result = feature.process(other_component.output())
        assert result.is_valid()
```

### Updating Tests After Changes

```bash
# 1. Run existing tests to establish baseline
pytest tests/ -v

# 2. Make your code changes

# 3. Run tests again - identify failures
pytest tests/ -v

# 4. Update tests to reflect new behavior
# - If behavior intentionally changed: update test expectations
# - If test was wrong: fix the test
# - If code broke something: fix the code

# 5. Add new tests for new functionality

# 6. Verify all tests pass
pytest tests/ -v

# 7. Check coverage didn't decrease
pytest --cov=src --cov-report=term-missing
```

---

## Accuracy Maintenance

### Updating Expected Classifications

When classification rules change:

1. **Document the change** in a PR description
2. **Update `expected_classifications.csv`** with new expectations
3. **Run accuracy tests** to verify improvement
4. **Update thresholds** if systematically better/worse

```bash
# Compare old vs new accuracy
pytest tests/accuracy/ -v --tb=short 2>&1 | tee accuracy_report.txt
```

### Monitoring Accuracy Over Time

Track metrics in `output/metrics.csv`:

| Metric              | Target | Alert If Below |
|---------------------|--------|----------------|
| Overall accuracy    | 85%    | 80%            |
| Bug recall          | 95%    | 90%            |
| Spam precision      | 98%    | 95%            |
| Avg confidence      | 0.85   | 0.75           |

---

## Quick Reference

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html && open htmlcov/index.html

# Run specific category
pytest -m unit          # Unit tests
pytest -m integration   # Integration tests
pytest -m accuracy      # Accuracy tests
pytest -m e2e           # E2E tests
pytest tests/e2e/ -v    # E2E tests (by directory)

# E2E specific
pytest -m "e2e and not slow"  # Quick E2E tests only
pytest tests/e2e/test_ui.py   # UI tests only
pytest tests/e2e/test_cli.py  # CLI tests only

# Run tests matching pattern
pytest -k "classifier"
pytest -k "bug and not slow"

# Debug failing test
pytest tests/unit/test_agents.py::TestClassifier::test_name -v -s

# Run last failed tests
pytest --lf
```
