"""Tests for create_workout_tool."""
import pytest
import responses
from unittest.mock import Mock, patch
from datetime import datetime

from src.tools.create_workout_tool import execute, _validate_workout_params


class TestValidateWorkoutParams:
    """Test workout parameter validation."""

    def test_valid_params_return_success(self, mock_config):
        """Should return True for valid parameters."""
        is_valid, error = _validate_workout_params(
            client_ftp=250,
            workout_duration=3600,
            workout_type="Sweet Spot",
            config=mock_config
        )

        assert is_valid is True
        assert error is None

    def test_missing_client_ftp(self, mock_config):
        """Should reject missing client_ftp."""
        is_valid, error = _validate_workout_params(
            client_ftp=None,
            workout_duration=3600,
            workout_type="Sweet Spot",
            config=mock_config
        )

        assert is_valid is False
        assert "client_ftp is required" in error

    def test_missing_workout_duration(self, mock_config):
        """Should reject missing workout_duration."""
        is_valid, error = _validate_workout_params(
            client_ftp=250,
            workout_duration=None,
            workout_type="Sweet Spot",
            config=mock_config
        )

        assert is_valid is False
        assert "workout_duration is required" in error

    def test_missing_workout_type(self, mock_config):
        """Should reject missing workout_type."""
        is_valid, error = _validate_workout_params(
            client_ftp=250,
            workout_duration=3600,
            workout_type=None,
            config=mock_config
        )

        assert is_valid is False
        assert "workout_type is required" in error

    def test_ftp_below_minimum(self, mock_config):
        """Should reject FTP below minimum threshold."""
        is_valid, error = _validate_workout_params(
            client_ftp=40,  # Below min of 50
            workout_duration=3600,
            workout_type="Sweet Spot",
            config=mock_config
        )

        assert is_valid is False
        assert "at least 50W" in error

    def test_ftp_above_maximum(self, mock_config):
        """Should reject FTP above maximum threshold."""
        is_valid, error = _validate_workout_params(
            client_ftp=700,  # Above max of 600
            workout_duration=3600,
            workout_type="Sweet Spot",
            config=mock_config
        )

        assert is_valid is False
        assert "at most 600W" in error

    def test_ftp_at_minimum_boundary(self, mock_config):
        """Should accept FTP at minimum boundary."""
        is_valid, error = _validate_workout_params(
            client_ftp=50,  # Exactly at min
            workout_duration=3600,
            workout_type="Sweet Spot",
            config=mock_config
        )

        assert is_valid is True

    def test_ftp_at_maximum_boundary(self, mock_config):
        """Should accept FTP at maximum boundary."""
        is_valid, error = _validate_workout_params(
            client_ftp=600,  # Exactly at max
            workout_duration=3600,
            workout_type="Sweet Spot",
            config=mock_config
        )

        assert is_valid is True

    def test_duration_below_minimum(self, mock_config):
        """Should reject duration below minimum (1 minute)."""
        is_valid, error = _validate_workout_params(
            client_ftp=250,
            workout_duration=30,  # Below min of 60
            workout_type="Sweet Spot",
            config=mock_config
        )

        assert is_valid is False
        assert "at least 60s" in error

    def test_duration_above_maximum(self, mock_config):
        """Should reject duration above maximum (4 hours)."""
        is_valid, error = _validate_workout_params(
            client_ftp=250,
            workout_duration=20000,  # Above max of 14400
            workout_type="Sweet Spot",
            config=mock_config
        )

        assert is_valid is False
        assert "at most 14400s" in error

    def test_duration_at_boundaries(self, mock_config):
        """Should accept duration at min and max boundaries."""
        # At minimum
        is_valid, _ = _validate_workout_params(60, 60, "Type", mock_config)
        assert is_valid is True

        # At maximum
        is_valid, _ = _validate_workout_params(250, 14400, "Type", mock_config)
        assert is_valid is True

    def test_invalid_ftp_type(self, mock_config):
        """Should reject non-integer FTP."""
        is_valid, error = _validate_workout_params(
            client_ftp="250",  # String instead of int
            workout_duration=3600,
            workout_type="Sweet Spot",
            config=mock_config
        )

        assert is_valid is False
        assert "must be an integer" in error

    def test_invalid_duration_type(self, mock_config):
        """Should reject non-integer duration."""
        is_valid, error = _validate_workout_params(
            client_ftp=250,
            workout_duration=3600.5,  # Float instead of int
            workout_type="Sweet Spot",
            config=mock_config
        )

        assert is_valid is False
        assert "must be an integer" in error

    def test_invalid_workout_type(self, mock_config):
        """Should reject non-string workout type."""
        is_valid, error = _validate_workout_params(
            client_ftp=250,
            workout_duration=3600,
            workout_type=123,  # Integer instead of string
            config=mock_config
        )

        assert is_valid is False
        assert "must be a string" in error

    def test_empty_workout_type(self, mock_config):
        """Should reject empty workout type string."""
        is_valid, error = _validate_workout_params(
            client_ftp=250,
            workout_duration=3600,
            workout_type="   ",  # Whitespace only
            config=mock_config
        )

        assert is_valid is False
        assert "cannot be empty" in error


class TestExecute:
    """Test create_workout_tool execute function."""

    @responses.activate
    def test_successful_workout_creation(self, mock_config, sample_zwo_content):
        """Should create, save, and upload workout successfully."""
        # Mock intervals.icu upload
        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            json=[{"id": "event-123", "name": "Sweet Spot Workout"}],
            status=200
        )

        # Create actual workout file so upload_workout can read it
        workout_path = mock_config.workouts_dir / "workout.zwo"
        workout_path.write_text(sample_zwo_content)

        # Create mock coach service
        mock_coach = Mock()
        mock_coach.workout_generator = Mock()
        mock_coach.workout_generator.generate_workout.return_value = sample_zwo_content
        mock_coach.workout_generator.save_workout.return_value = str(workout_path)

        args = {
            "client_ftp": 250,
            "workout_duration": 3600,
            "workout_type": "Sweet Spot"
        }

        result = execute(args, mock_config, mock_coach)

        assert result["success"] is True
        assert result["event_id"] == "event-123"
        assert "workout_file" in result
        assert "scheduled_time" in result

    def test_validation_failure_returns_error(self, mock_config):
        """Should return error for invalid parameters."""
        mock_coach = Mock()

        args = {
            "client_ftp": 30,  # Below minimum
            "workout_duration": 3600,
            "workout_type": "Sweet Spot"
        }

        result = execute(args, mock_config, mock_coach)

        assert result["success"] is False
        assert "Invalid parameters" in result["error"]
        # Workout generator should not be called
        mock_coach.workout_generator.generate_workout.assert_not_called()

    def test_missing_parameter_returns_error(self, mock_config):
        """Should return error for missing required parameters."""
        mock_coach = Mock()

        args = {
            "client_ftp": 250,
            # Missing workout_duration and workout_type
        }

        result = execute(args, mock_config, mock_coach)

        assert result["success"] is False
        assert "required" in result["error"]

    def test_workout_generation_error(self, mock_config):
        """Should handle workout generation failures."""
        mock_coach = Mock()
        mock_coach.workout_generator = Mock()
        mock_coach.workout_generator.generate_workout.side_effect = Exception("LLM API error")

        args = {
            "client_ftp": 250,
            "workout_duration": 3600,
            "workout_type": "Sweet Spot"
        }

        result = execute(args, mock_config, mock_coach)

        assert result["success"] is False
        assert "LLM API error" in result["error"]

    @responses.activate
    def test_upload_error(self, mock_config, sample_zwo_content):
        """Should handle upload failures."""
        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            status=500
        )

        # Create actual workout file so upload_workout can read it
        workout_path = mock_config.workouts_dir / "workout.zwo"
        workout_path.write_text(sample_zwo_content)

        mock_coach = Mock()
        mock_coach.workout_generator = Mock()
        mock_coach.workout_generator.generate_workout.return_value = sample_zwo_content
        mock_coach.workout_generator.save_workout.return_value = str(workout_path)

        args = {
            "client_ftp": 250,
            "workout_duration": 3600,
            "workout_type": "Sweet Spot"
        }

        # Prevent retries from taking too long
        with patch("src.utils.retry.time.sleep"):
            result = execute(args, mock_config, mock_coach)

        assert result["success"] is False

    @responses.activate
    def test_schedule_time_uses_config_hours(self, mock_config, sample_zwo_content):
        """Should schedule workout using configured hours ahead."""
        mock_config.workout_schedule_hours = 2

        responses.add(
            responses.POST,
            f"{mock_config.intervals_base_url}/athlete/{mock_config.default_athlete_id}/events/bulk",
            json=[{"id": "event-123"}],
            status=200
        )

        # Create actual workout file so upload_workout can read it
        workout_path = mock_config.workouts_dir / "workout.zwo"
        workout_path.write_text(sample_zwo_content)

        mock_coach = Mock()
        mock_coach.workout_generator = Mock()
        mock_coach.workout_generator.generate_workout.return_value = sample_zwo_content
        mock_coach.workout_generator.save_workout.return_value = str(workout_path)

        args = {
            "client_ftp": 250,
            "workout_duration": 3600,
            "workout_type": "Sweet Spot"
        }

        result = execute(args, mock_config, mock_coach)

        # Verify scheduled time is approximately 2 hours from now
        scheduled = datetime.fromisoformat(result["scheduled_time"])
        expected_min = datetime.now()
        # Allow some tolerance
        assert (scheduled - expected_min).total_seconds() >= 7000  # ~2 hours
