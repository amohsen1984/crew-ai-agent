"""Tests for FastAPI backend."""

import pytest
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


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Health check should return healthy status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self, client):
        """Root endpoint should return API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data


class TestTicketsEndpoint:
    """Test tickets endpoints."""

    def test_get_tickets_empty(self, client):
        """Get tickets should return empty list when no tickets."""
        response = client.get("/api/v1/tickets")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_tickets_with_filters(self, client):
        """Get tickets should accept category and priority filters."""
        response = client.get(
            "/api/v1/tickets",
            params={"category": "Bug", "priority": "High", "limit": 10},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_ticket_not_found(self, client):
        """Get non-existent ticket should return 404."""
        response = client.get("/api/v1/tickets/nonexistent-id")
        assert response.status_code == 404


class TestMetricsEndpoint:
    """Test metrics endpoint."""

    def test_get_metrics(self, client):
        """Get metrics should return metrics data."""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data


class TestStatsEndpoint:
    """Test stats endpoint."""

    def test_get_stats(self, client):
        """Get stats should return statistics."""
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_tickets" in data
        assert "by_category" in data
        assert "by_priority" in data

