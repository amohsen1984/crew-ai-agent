"""Unit tests for tools."""

import json
import pytest
import pandas as pd
from pathlib import Path

from tools.csv_tools import read_csv_tool, write_csv_tool


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
        "app_version": ["2.1.3", "2.1.3"],
    })
    df.to_csv(csv_path, index=False)
    return csv_path


class TestReadCSVTool:
    """Test read_csv_tool function."""

    def test_reads_valid_csv(self, sample_csv):
        """Should read and parse valid CSV file."""
        result = read_csv_tool(str(sample_csv))
        data = json.loads(result)
        assert "records" in data
        assert len(data["records"]) == 2
        assert data["records"][0]["review_id"] == "REV001"

    def test_file_not_found_returns_error(self):
        """Should return error message for missing file."""
        result = read_csv_tool("/nonexistent/path.csv")
        data = json.loads(result)
        assert "error" in data

    def test_empty_csv_returns_empty_list(self, tmp_path):
        """Should handle empty CSV gracefully."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("col1,col2\n")
        result = read_csv_tool(str(empty_csv))
        data = json.loads(result)
        assert "records" in data or "error" in data


class TestWriteCSVTool:
    """Test write_csv_tool function."""

    def test_writes_valid_data(self, tmp_path):
        """Should write data to CSV file."""
        output_path = tmp_path / "output.csv"
        data = json.dumps({
            "records": [
                {"ticket_id": "TKT-001", "title": "Bug report"},
                {"ticket_id": "TKT-002", "title": "Feature request"},
            ]
        })
        result = write_csv_tool(str(output_path), data)
        result_data = json.loads(result)
        assert result_data.get("success") is True
        assert output_path.exists()

        df = pd.read_csv(output_path)
        assert len(df) == 2

    def test_appends_to_existing_file(self, tmp_path):
        """Should append to existing CSV without overwriting."""
        output_path = tmp_path / "output.csv"

        # Write initial data
        data1 = json.dumps({"records": [{"id": "1"}]})
        write_csv_tool(str(output_path), data1)

        # Append more data
        data2 = json.dumps({"records": [{"id": "2"}]})
        write_csv_tool(str(output_path), data2, append=True)

        df = pd.read_csv(output_path)
        assert len(df) == 2

