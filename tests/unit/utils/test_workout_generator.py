"""Tests for WorkoutGenerator utility."""
import pytest
import re
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from src.utils.workout_generator import WorkoutGenerator


class TestWorkoutGeneratorInit:
    """Test WorkoutGenerator initialization."""

    def test_init_loads_prompt_template(self, mock_config):
        """Should load workout generator prompt from file."""
        mock_llm = Mock()

        generator = WorkoutGenerator(mock_llm, mock_config)

        assert generator.workout_prompt_template == "Generate ZWO workouts."
        assert generator.llm_client is mock_llm
        assert generator.config is mock_config

    def test_init_raises_on_missing_prompt(self, mock_config):
        """Should raise error if prompt file doesn't exist."""
        mock_llm = Mock()
        # Remove the prompt file
        (mock_config.project_root / "prompts" / "workout_generator_prompt.txt").unlink()

        with pytest.raises(FileNotFoundError):
            WorkoutGenerator(mock_llm, mock_config)


class TestValidateZwo:
    """Test ZWO validation logic."""

    def test_valid_zwo_with_workout_file_tags(self, mock_config, sample_zwo_content):
        """Should return True for valid ZWO content."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        assert generator._validate_zwo(sample_zwo_content) is True

    def test_invalid_zwo_missing_opening_tag(self, mock_config):
        """Should return False when opening tag is missing."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        invalid_content = """<?xml version="1.0"?>
        <workout>some content</workout>
        </workout_file>"""

        assert generator._validate_zwo(invalid_content) is False

    def test_invalid_zwo_missing_closing_tag(self, mock_config):
        """Should return False when closing tag is missing."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        invalid_content = """<?xml version="1.0"?>
        <workout_file>
        <workout>some content</workout>"""

        assert generator._validate_zwo(invalid_content) is False

    def test_invalid_zwo_empty_content(self, mock_config):
        """Should return False for empty content."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        assert generator._validate_zwo("") is False

    def test_valid_zwo_minimal(self, mock_config):
        """Should return True for minimal valid structure."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        minimal_content = "<workout_file></workout_file>"
        assert generator._validate_zwo(minimal_content) is True


class TestGenerateWorkout:
    """Test workout generation."""

    def test_generates_workout_with_correct_parameters(self, mock_config, sample_zwo_content):
        """Should call LLM with correct prompt and parameters."""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = sample_zwo_content
        mock_llm.generate.return_value = mock_response

        generator = WorkoutGenerator(mock_llm, mock_config)
        result = generator.generate_workout(
            client_ftp=250,
            workout_duration=3600,
            workout_type="Sweet Spot"
        )

        # Verify LLM was called with correct parameters
        mock_llm.generate.assert_called_once()
        call_kwargs = mock_llm.generate.call_args.kwargs

        assert call_kwargs["model"] == mock_config.model_name
        assert call_kwargs["temperature"] == mock_config.temperature

        # Verify messages contain FTP, duration, and type
        messages = call_kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "250W" in messages[1]["content"]
        assert "3600 seconds" in messages[1]["content"]
        assert "Sweet Spot" in messages[1]["content"]

    def test_returns_zwo_content(self, mock_config, sample_zwo_content):
        """Should return the generated ZWO content."""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = sample_zwo_content
        mock_llm.generate.return_value = mock_response

        generator = WorkoutGenerator(mock_llm, mock_config)
        result = generator.generate_workout(250, 3600, "Sweet Spot")

        assert result == sample_zwo_content

    def test_strips_whitespace_from_response(self, mock_config, sample_zwo_content):
        """Should strip leading/trailing whitespace from response."""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = f"\n\n  {sample_zwo_content}  \n\n"
        mock_llm.generate.return_value = mock_response

        generator = WorkoutGenerator(mock_llm, mock_config)
        result = generator.generate_workout(250, 3600, "Sweet Spot")

        assert result == sample_zwo_content

    def test_raises_on_invalid_zwo_response(self, mock_config):
        """Should raise ValueError when LLM returns invalid ZWO."""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "This is not valid ZWO content"
        mock_llm.generate.return_value = mock_response

        generator = WorkoutGenerator(mock_llm, mock_config)

        with pytest.raises(ValueError, match="missing required XML structure"):
            generator.generate_workout(250, 3600, "Sweet Spot")

    def test_propagates_llm_exception(self, mock_config):
        """Should propagate exceptions from LLM client."""
        mock_llm = Mock()
        mock_llm.generate.side_effect = Exception("API error")

        generator = WorkoutGenerator(mock_llm, mock_config)

        with pytest.raises(Exception, match="API error"):
            generator.generate_workout(250, 3600, "Sweet Spot")

    def test_includes_duration_in_minutes(self, mock_config, sample_zwo_content):
        """Should include duration in both seconds and minutes."""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = sample_zwo_content
        mock_llm.generate.return_value = mock_response

        generator = WorkoutGenerator(mock_llm, mock_config)
        generator.generate_workout(250, 3600, "Sweet Spot")

        user_prompt = mock_llm.generate.call_args.kwargs["messages"][1]["content"]
        assert "60 minutes" in user_prompt


class TestSaveWorkout:
    """Test workout saving functionality."""

    def test_saves_workout_to_file(self, mock_config, sample_zwo_content):
        """Should save ZWO content to file in workouts directory."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        filepath = generator.save_workout(sample_zwo_content, "Sweet Spot")

        assert Path(filepath).exists()
        assert Path(filepath).read_text() == sample_zwo_content

    def test_creates_workouts_directory(self, mock_config, sample_zwo_content):
        """Should create workouts directory if it doesn't exist."""
        mock_llm = Mock()
        # Remove the workouts directory
        mock_config.workouts_dir.rmdir()

        generator = WorkoutGenerator(mock_llm, mock_config)
        filepath = generator.save_workout(sample_zwo_content, "Sweet Spot")

        assert mock_config.workouts_dir.exists()
        assert Path(filepath).exists()

    def test_filename_includes_workout_type(self, mock_config, sample_zwo_content):
        """Should include sanitized workout type in filename."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        filepath = generator.save_workout(sample_zwo_content, "Sweet Spot")

        filename = Path(filepath).name
        assert "sweet_spot" in filename
        assert filename.endswith(".zwo")

    def test_filename_includes_timestamp(self, mock_config, sample_zwo_content):
        """Should include timestamp in filename."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        filepath = generator.save_workout(sample_zwo_content, "Sweet Spot")

        filename = Path(filepath).name
        # Should match pattern like: sweet_spot_20240115_093000.zwo
        assert re.match(r"sweet_spot_\d{8}_\d{6}\.zwo", filename)

    def test_sanitizes_workout_type_for_filename(self, mock_config, sample_zwo_content):
        """Should sanitize special characters from workout type."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        filepath = generator.save_workout(sample_zwo_content, "VO2 Max / Intervals!")

        filename = Path(filepath).name
        # Special characters should be replaced with underscores
        assert "vo2_max_intervals" in filename
        assert "/" not in filename
        assert "!" not in filename

    def test_returns_filepath_as_string(self, mock_config, sample_zwo_content):
        """Should return the filepath as a string."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        filepath = generator.save_workout(sample_zwo_content, "Sweet Spot")

        assert isinstance(filepath, str)
        assert filepath.startswith(str(mock_config.workouts_dir))

    def test_handles_empty_workout_type(self, mock_config, sample_zwo_content):
        """Should handle empty workout type gracefully."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        filepath = generator.save_workout(sample_zwo_content, "")

        filename = Path(filepath).name
        # Should still have timestamp and extension
        assert filename.endswith(".zwo")
        assert re.match(r"_?\d{8}_\d{6}\.zwo", filename)

    def test_handles_workout_type_with_only_special_chars(self, mock_config, sample_zwo_content):
        """Should handle workout type with only special characters."""
        mock_llm = Mock()
        generator = WorkoutGenerator(mock_llm, mock_config)

        filepath = generator.save_workout(sample_zwo_content, "!!!//@@@")

        filename = Path(filepath).name
        assert filename.endswith(".zwo")
