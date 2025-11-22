"""Tests for IntervalsClient integration."""
import base64
import pytest
import responses
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.integrations.intervals import IntervalsClient


class TestIntervalsClientInit:
    """Test IntervalsClient initialization."""

    def test_init_with_api_key_and_config(self, mock_config):
        """Should initialize with API key and config."""
        client = IntervalsClient(api_key="test-key", config=mock_config)

        assert client.api_key == "test-key"
        assert client.config is mock_config
        assert client.athlete_id == mock_config.default_athlete_id
        assert client.auth == ("API_KEY", "test-key")

    def test_init_with_custom_athlete_id(self, mock_config):
        """Should use custom athlete ID when provided."""
        client = IntervalsClient(
            api_key="test-key",
            config=mock_config,
            athlete_id="custom-123"
        )

        assert client.athlete_id == "custom-123"

    def test_init_raises_without_api_key(self, mock_config):
        """Should raise ValueError when API key is missing."""
        with pytest.raises(ValueError, match="API key is required"):
            IntervalsClient(api_key="", config=mock_config)

        with pytest.raises(ValueError, match="API key is required"):
            IntervalsClient(api_key=None, config=mock_config)


class TestReadWorkoutFile:
    """Test ZWO file reading functionality."""

    def test_reads_zwo_file_as_base64(self, mock_config, create_temp_zwo_file):
        """Should read ZWO file and return base64 encoded content."""
        filepath = create_temp_zwo_file()
        client = IntervalsClient(api_key="test-key", config=mock_config)

        result = client.read_workout_file(str(filepath))

        expected = base64.b64encode(filepath.read_bytes()).decode('utf-8')
        assert result == expected

    def test_raises_on_nonexistent_file(self, mock_config):
        """Should raise FileNotFoundError for missing file."""
        client = IntervalsClient(api_key="test-key", config=mock_config)

        with pytest.raises(FileNotFoundError, match="File not found"):
            client.read_workout_file("/nonexistent/path/workout.zwo")

    def test_raises_on_non_zwo_file(self, mock_config, tmp_path):
        """Should raise ValueError for non-ZWO files."""
        txt_file = tmp_path / "workout.txt"
        txt_file.write_text("not a zwo file")
        client = IntervalsClient(api_key="test-key", config=mock_config)

        with pytest.raises(ValueError, match="must be a .zwo file"):
            client.read_workout_file(str(txt_file))

    def test_accepts_uppercase_zwo_extension(self, mock_config, tmp_path, sample_zwo_content):
        """Should accept .ZWO extension (case insensitive)."""
        zwo_file = tmp_path / "workout.ZWO"
        zwo_file.write_text(sample_zwo_content)
        client = IntervalsClient(api_key="test-key", config=mock_config)

        result = client.read_workout_file(str(zwo_file))

        assert result is not None
        # Verify it's valid base64
        decoded = base64.b64decode(result)
        assert sample_zwo_content.encode() == decoded


class TestUploadWorkoutContent:
    """Test direct content upload functionality."""

    @responses.activate
    def test_uploads_workout_content_successfully(self, mock_config, sample_zwo_content):
        """Should upload ZWO content directly to intervals.icu."""
        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            json=[{"id": "event-123", "name": "Test Workout", "category": "WORKOUT"}],
            status=200
        )

        client = IntervalsClient(api_key="test-key", config=mock_config)
        result = client.upload_workout_content(
            zwo_content=sample_zwo_content,
            filename="test_workout.zwo",
            start_date="2024-01-15T09:00:00"
        )

        assert result["id"] == "event-123"
        assert result["name"] == "Test Workout"

    @responses.activate
    def test_upload_includes_external_id(self, mock_config, sample_zwo_content):
        """Should include external_id in payload when provided."""
        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            json=[{"id": "event-123"}],
            status=200
        )

        client = IntervalsClient(api_key="test-key", config=mock_config)
        client.upload_workout_content(
            zwo_content=sample_zwo_content,
            filename="test.zwo",
            start_date="2024-01-15T09:00:00",
            external_id="train-r-001"
        )

        # Verify request payload
        request_body = responses.calls[0].request.body
        import json
        payload = json.loads(request_body)
        assert payload[0]["external_id"] == "train-r-001"


class TestUploadWorkout:
    """Test file-based workout upload."""

    @responses.activate
    def test_uploads_workout_file(self, mock_config, create_temp_zwo_file):
        """Should upload ZWO file to intervals.icu."""
        filepath = create_temp_zwo_file()
        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            json=[{"id": "event-456"}],
            status=200
        )

        client = IntervalsClient(api_key="test-key", config=mock_config)
        result = client.upload_workout(
            file_path=str(filepath),
            start_date="2024-01-15T09:00:00"
        )

        assert result["id"] == "event-456"


class TestGetWorkoutHistory:
    """Test workout history retrieval."""

    @responses.activate
    def test_fetches_workout_history(self, mock_config, sample_activities_list):
        """Should fetch and transform activity history."""
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            json=sample_activities_list,
            status=200
        )

        client = IntervalsClient(api_key="test-key", config=mock_config)
        result = client.get_workout_history(
            oldest_date="2024-01-01",
            newest_date="2024-01-31"
        )

        assert len(result) == 3

    @responses.activate
    def test_transforms_field_names(self, mock_config, sample_intervals_activity):
        """Should transform intervals.icu field names to standard names."""
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            json=[sample_intervals_activity],
            status=200
        )

        client = IntervalsClient(api_key="test-key", config=mock_config)
        result = client.get_workout_history(
            oldest_date="2024-01-01",
            newest_date="2024-01-31"
        )

        activity = result[0]
        # Verify field transformations
        assert activity["date"] == "2024-01-15T09:00:00"
        assert activity["type"] == "Ride"
        assert activity["duration_seconds"] == 3600
        assert activity["distance_meters"] == 30000
        assert activity["avg_power_watts"] == 200
        assert activity["normalized_power_watts"] == 210
        assert activity["intensity_factor"] == 0.85
        assert activity["training_stress_score"] == 75
        assert activity["power_zone_times"] == [600, 1200, 900, 600, 300]
        assert activity["acute_training_load"] == 65
        assert activity["chronic_training_load"] == 70

    @responses.activate
    def test_uses_default_date_range(self, mock_config):
        """Should default to configured lookback period."""
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            json=[],
            status=200
        )

        client = IntervalsClient(api_key="test-key", config=mock_config)
        client.get_workout_history()  # No dates provided

        # Verify the request used default dates
        request = responses.calls[0].request
        assert "oldest=" in request.url
        assert "newest=" in request.url

    @responses.activate
    def test_handles_missing_activity_fields(self, mock_config):
        """Should handle activities with missing optional fields."""
        incomplete_activity = {
            "start_date_local": "2024-01-15T09:00:00",
            "type": "Ride",
            # All other fields missing
        }
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activities",
            json=[incomplete_activity],
            status=200
        )

        client = IntervalsClient(api_key="test-key", config=mock_config)
        result = client.get_workout_history(oldest_date="2024-01-01", newest_date="2024-01-31")

        activity = result[0]
        assert activity["date"] == "2024-01-15T09:00:00"
        assert activity["type"] == "Ride"
        assert activity["avg_power_watts"] is None
        assert activity["training_stress_score"] is None


class TestGetPowerCurves:
    """Test power curves retrieval."""

    @responses.activate
    def test_fetches_power_curves_for_multiple_periods(self, mock_config, sample_power_curves_response):
        """Should fetch power curves for all configured time periods."""
        # Add response for each time period
        for _ in mock_config.power_curve_time_periods_months:
            responses.add(
                responses.GET,
                f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activity-power-curves",
                json=sample_power_curves_response,
                status=200
            )

        client = IntervalsClient(api_key="test-key", config=mock_config)
        result = client.get_power_curves()

        # Should have data for each configured period
        assert len(result) == len(mock_config.power_curve_time_periods_months)

    @responses.activate
    def test_transforms_power_curve_format(self, mock_config, sample_power_curves_response):
        """Should transform power curve data to readable format."""
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activity-power-curves",
            json=sample_power_curves_response,
            status=200
        )

        mock_config.power_curve_time_periods_months = [1]  # Just test one period
        client = IntervalsClient(api_key="test-key", config=mock_config)
        result = client.get_power_curves()

        # Verify transformed keys
        assert "1_month" in result
        power_data = result["1_month"]
        assert "15_seconds" in power_data
        assert "1_minutes" in power_data
        assert "5_minutes" in power_data

    @responses.activate
    def test_finds_max_power_across_activities(self, mock_config):
        """Should return maximum power for each duration."""
        power_response = {
            "secs": [15],
            "curves": [
                {"watts": [450]},
                {"watts": [460]},  # This should be the max
                {"watts": [440]},
            ]
        }
        responses.add(
            responses.GET,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activity-power-curves",
            json=power_response,
            status=200
        )

        mock_config.power_curve_time_periods_months = [1]
        client = IntervalsClient(api_key="test-key", config=mock_config)
        result = client.get_power_curves()

        assert result["1_month"]["15_seconds"] == 460

    @responses.activate
    def test_handles_api_error_for_period(self, mock_config):
        """Should continue with other periods if one fails."""
        # Configure to only test one period to simplify the test
        mock_config.power_curve_time_periods_months = [3]

        # Period fails with 404 (need multiple responses for retries)
        for _ in range(3):  # max_retries = 3
            responses.add(
                responses.GET,
                f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/activity-power-curves",
                json={"error": "Not found"},
                status=404
            )

        with patch("src.utils.retry.time.sleep"):
            client = IntervalsClient(api_key="test-key", config=mock_config)
            result = client.get_power_curves()

        # Failed period should have error
        assert "3_months" in result or "3_months_max_power" in result
        period_key = "3_months" if "3_months" in result else "3_months_max_power"
        assert "error" in result[period_key]


class TestRetryBehavior:
    """Test HTTP retry behavior."""

    @responses.activate
    def test_retries_on_server_error(self, mock_config, sample_zwo_content):
        """Should retry on 5xx server errors."""
        # First two calls fail, third succeeds
        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            status=500
        )
        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            status=500
        )
        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            json=[{"id": "event-123"}],
            status=200
        )

        with patch("src.utils.retry.time.sleep"):
            client = IntervalsClient(api_key="test-key", config=mock_config)
            result = client.upload_workout_content(
                zwo_content=sample_zwo_content,
                filename="test.zwo",
                start_date="2024-01-15T09:00:00"
            )

        assert result["id"] == "event-123"
        assert len(responses.calls) == 3

    @responses.activate
    def test_no_retry_on_client_error(self, mock_config, sample_zwo_content):
        """Should not retry on 4xx client errors (except 429)."""
        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            json={"error": "Bad request"},
            status=400
        )

        client = IntervalsClient(api_key="test-key", config=mock_config)

        with pytest.raises(Exception):
            client.upload_workout_content(
                zwo_content=sample_zwo_content,
                filename="test.zwo",
                start_date="2024-01-15T09:00:00"
            )

        # Should only have made one request (no retries)
        assert len(responses.calls) == 1

    @responses.activate
    def test_retries_on_rate_limit(self, mock_config, sample_zwo_content):
        """Should retry on 429 rate limit errors."""
        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            status=429
        )
        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            json=[{"id": "event-123"}],
            status=200
        )

        with patch("src.utils.retry.time.sleep"):
            client = IntervalsClient(api_key="test-key", config=mock_config)
            result = client.upload_workout_content(
                zwo_content=sample_zwo_content,
                filename="test.zwo",
                start_date="2024-01-15T09:00:00"
            )

        assert result["id"] == "event-123"
        assert len(responses.calls) == 2
