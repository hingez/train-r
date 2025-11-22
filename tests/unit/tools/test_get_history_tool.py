"""Tests for get_history_tool."""
import json
import pytest
import responses
from pathlib import Path
from unittest.mock import Mock, patch

from src.tools.get_history_tool import execute


class TestExecute:
    """Test get_history_tool execute function."""

    @responses.activate
    def test_fetches_history_successfully(self, mock_config, sample_activities_list):
        """Should fetch and save workout history."""
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            json=sample_activities_list,
            status=200
        )

        args = {
            "oldest_date": "2024-01-01",
            "newest_date": "2024-01-31"
        }

        result = execute(args, mock_config, coach_service=None)

        assert result["success"] is True
        assert result["workout_count"] == 3
        assert "saved_to" in result

    @responses.activate
    def test_saves_history_to_file(self, mock_config, sample_activities_list):
        """Should save history data to JSON file."""
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            json=sample_activities_list,
            status=200
        )

        args = {
            "oldest_date": "2024-01-01",
            "newest_date": "2024-01-31"
        }

        result = execute(args, mock_config, coach_service=None)

        # Verify file was created and contains valid JSON
        saved_path = Path(result["saved_to"])
        assert saved_path.exists()

        with open(saved_path) as f:
            saved_data = json.load(f)

        # Should have transformed activity data
        assert len(saved_data) == 3

    @responses.activate
    def test_creates_history_directory(self, mock_config, sample_activities_list):
        """Should create history directory if it doesn't exist."""
        # Remove history directory
        if mock_config.history_dir.exists():
            mock_config.history_dir.rmdir()

        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            json=sample_activities_list,
            status=200
        )

        args = {"oldest_date": "2024-01-01", "newest_date": "2024-01-31"}
        result = execute(args, mock_config, coach_service=None)

        assert result["success"] is True
        assert Path(result["saved_to"]).exists()

    @responses.activate
    def test_handles_optional_date_parameters(self, mock_config):
        """Should work with optional date parameters."""
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            json=[],
            status=200
        )

        # No dates provided - should use defaults
        args = {}
        result = execute(args, mock_config, coach_service=None)

        assert result["success"] is True
        assert result["workout_count"] == 0

    @responses.activate
    def test_handles_api_error(self, mock_config):
        """Should return error on API failure."""
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            status=500
        )

        args = {"oldest_date": "2024-01-01", "newest_date": "2024-01-31"}

        with patch("src.utils.retry.time.sleep"):
            result = execute(args, mock_config, coach_service=None)

        assert result["success"] is False
        assert "error" in result

    @responses.activate
    def test_filename_includes_timestamp(self, mock_config):
        """Should include timestamp in saved filename."""
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            json=[],
            status=200
        )

        args = {}
        result = execute(args, mock_config, coach_service=None)

        filename = Path(result["saved_to"]).name
        assert filename.startswith("history_")
        assert filename.endswith(".json")

    @responses.activate
    def test_does_not_require_coach_service(self, mock_config):
        """Should work without coach_service parameter."""
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            json=[],
            status=200
        )

        # coach_service explicitly set to None
        result = execute({}, mock_config, coach_service=None)

        assert result["success"] is True

    @responses.activate
    def test_returns_confirmation_message(self, mock_config):
        """Should return appropriate confirmation message."""
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            json=[],
            status=200
        )

        result = execute({}, mock_config, coach_service=None)

        assert result["message"] == "history fetched"
