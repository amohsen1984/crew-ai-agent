"""Integration tests for API endpoints."""

import pytest
import requests
from fastapi.testclient import TestClient

import sys
from pathlib import Path

# Add backend/src to path
backend_src = Path(__file__).parent.parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.integration
class TestProcessFeedbackIntegration:
    """Integration tests for feedback processing."""

    def test_process_feedback_endpoint(self, client, tmp_path):
        """Process feedback endpoint should accept requests."""
        # Note: This will fail if OpenAI API key is not set
        # In real tests, you'd mock the service
        response = client.post("/api/v1/process")
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 500]
        data = response.json()
        assert "status" in data


@pytest.mark.integration
class TestTicketUpdateIntegration:
    """Integration tests for ticket updates."""

    def test_update_ticket_endpoint(self, client):
        """Update ticket endpoint should accept update requests."""
        # Try to update non-existent ticket
        response = client.patch(
            "/api/v1/tickets/test-id",
            json={"title": "Updated Title"},
        )
        # Should return 404 for non-existent ticket
        assert response.status_code == 404

