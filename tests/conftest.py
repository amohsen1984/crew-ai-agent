"""Shared fixtures for tests."""

import sys
from pathlib import Path

import pytest

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))
# Now imports work directly: from crew import ...


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
            "app_version": "2.1.3",
        },
        {
            "review_id": "REV002",
            "platform": "Google Play",
            "rating": 5,
            "review_text": "Best productivity app I've ever used!",
            "user_name": "happy_user",
            "date": "2024-01-16",
            "app_version": "2.1.3",
        },
        {
            "review_id": "REV003",
            "platform": "App Store",
            "rating": 3,
            "review_text": "Good app but please add dark mode",
            "user_name": "feature_requester",
            "date": "2024-01-17",
            "app_version": "2.1.3",
        },
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
            "priority": "High",
        },
        {
            "email_id": "EMAIL002",
            "subject": "Feature Suggestion",
            "body": "It would be great if you could add calendar integration.",
            "sender_email": "user2@example.com",
            "timestamp": "2024-01-16T14:00:00",
            "priority": "",
        },
    ]

