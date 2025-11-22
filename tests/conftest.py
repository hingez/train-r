"""Shared pytest fixtures for Train-R tests."""
import json
import pytest
from pathlib import Path
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock
from typing import Optional

from src.config import AppConfig


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test file operations."""
    return tmp_path


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock AppConfig for testing without environment dependencies."""
    # Create required directories
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    tools_dir = tmp_path / "tools" / "definitions"
    tools_dir.mkdir(parents=True)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    workouts_dir = data_dir / "created_workouts"
    workouts_dir.mkdir()
    history_dir = data_dir / "workout_history"
    history_dir.mkdir()

    # Create a minimal system prompt file
    system_prompt = prompts_dir / "system_prompt.txt"
    system_prompt.write_text("You are a cycling coach.")

    # Create workout generator prompt
    workout_prompt = prompts_dir / "workout_generator_prompt.txt"
    workout_prompt.write_text("Generate ZWO workouts.")

    return AppConfig(
        llm_api_key="test-llm-key",
        intervals_api_key="test-intervals-key",
        project_root=tmp_path,
        prompts_dir=prompts_dir,
        data_dir=data_dir,
        logs_dir=logs_dir,
        tools_dir=tools_dir,
        workouts_dir=workouts_dir,
        history_dir=history_dir,
        model_name="test-model",
        temperature=0.0,
        llm_base_url="https://test-api.example.com/",
        intervals_base_url="https://test-intervals.example.com/api/v1",
        intervals_api_timeout=10,
        workout_min_ftp=50,
        workout_max_ftp=600,
        workout_min_duration=60,
        workout_max_duration=14400,
        history_default_lookback_days=365,
        power_curve_time_periods_months=[1, 3, 6],
        power_curve_durations_seconds=[15, 60, 300],
        default_athlete_id="test-athlete-123",
        max_tool_iterations=5,
        workout_schedule_hours=1,
    )


@pytest.fixture
def sample_zwo_content():
    """Sample valid ZWO workout content."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<workout_file>
    <author>Train-R</author>
    <name>Test Workout</name>
    <description>A test workout</description>
    <sportType>bike</sportType>
    <workout>
        <Warmup Duration="300" PowerLow="0.50" PowerHigh="0.75"/>
        <SteadyState Duration="600" Power="0.85"/>
        <Cooldown Duration="300" PowerLow="0.75" PowerHigh="0.50"/>
    </workout>
</workout_file>"""


@pytest.fixture
def sample_intervals_activity():
    """Sample activity response from intervals.icu API."""
    return {
        "id": "i12345",
        "start_date_local": "2024-01-15T09:00:00",
        "type": "Ride",
        "moving_time": 3600,
        "distance": 30000,
        "icu_average_watts": 200,
        "icu_weighted_avg_watts": 210,
        "icu_intensity": 0.85,
        "icu_training_load": 75,
        "icu_zone_times": [600, 1200, 900, 600, 300],
        "icu_atl": 65,
        "icu_ctl": 70,
    }


@pytest.fixture
def sample_activities_list(sample_intervals_activity):
    """List of sample activities for history tests."""
    activities = []
    for i in range(3):
        activity = sample_intervals_activity.copy()
        activity["id"] = f"i{12345 + i}"
        activity["start_date_local"] = f"2024-01-{15 + i}T09:00:00"
        activities.append(activity)
    return activities


@pytest.fixture
def sample_power_curves_response():
    """Sample power curves response from intervals.icu API."""
    return {
        "secs": [15, 60, 300],
        "curves": [
            {"watts": [450, 350, 280]},
            {"watts": [440, 340, 275]},
            {"watts": [460, 360, 285]},
        ]
    }


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM ChatCompletion response."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = "Test response from LLM"
    response.choices[0].message.tool_calls = None
    return response


@pytest.fixture
def mock_llm_response_with_tool_call():
    """Create a mock LLM response with a tool call."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = None

    # Create tool call
    tool_call = Mock()
    tool_call.id = "call_123"
    tool_call.function = Mock()
    tool_call.function.name = "create_one_off_workout"
    tool_call.function.arguments = json.dumps({
        "client_ftp": 250,
        "workout_duration": 3600,
        "workout_type": "Sweet Spot"
    })

    response.choices[0].message.tool_calls = [tool_call]
    return response


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    return client


@pytest.fixture
def sample_tool_definition():
    """Sample tool definition in OpenAI format."""
    return {
        "type": "function",
        "function": {
            "name": "create_one_off_workout",
            "description": "Create a single workout",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_ftp": {"type": "integer"},
                    "workout_duration": {"type": "integer"},
                    "workout_type": {"type": "string"}
                },
                "required": ["client_ftp", "workout_duration", "workout_type"]
            }
        }
    }


@pytest.fixture
def create_temp_zwo_file(tmp_path, sample_zwo_content):
    """Factory fixture to create temporary ZWO files."""
    def _create(filename="test_workout.zwo", content=None):
        filepath = tmp_path / filename
        filepath.write_text(content or sample_zwo_content)
        return filepath
    return _create
