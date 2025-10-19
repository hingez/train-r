"""Centralized model configuration for Gemini API."""
from dataclasses import dataclass
from typing import Optional
from google.genai.types import GenerateContentConfig

# Configuration constants
GEMINI_MODEL_NAME = "gemini-2.5-flash"
GEMINI_TEMPERATURE = 0
DEFAULT_WORKOUT_SCHEDULE_HOURS = 1
DEFAULT_ATHLETE_ID = "0"


@dataclass
class AppConfig:
    """Application configuration container.

    Attributes:
        gemini_api_key: API key for Google Gemini
        intervals_api_key: API key for intervals.icu
        workout_schedule_hours: Hours in the future to schedule workouts (default: 1)
    """
    gemini_api_key: str
    intervals_api_key: str
    workout_schedule_hours: int = DEFAULT_WORKOUT_SCHEDULE_HOURS


def get_model_name() -> str:
    """Get the model name to use for all requests."""
    return GEMINI_MODEL_NAME


def get_model_config(
    system_prompt: str,
    tools: Optional[list] = None,
    temperature: float = GEMINI_TEMPERATURE
) -> GenerateContentConfig:
    """Get the standard model configuration.

    Args:
        system_prompt: System instruction to provide to the model
        tools: List of Tool objects for function calling (optional)
        temperature: Model temperature (default 0 for deterministic output)

    Returns:
        GenerateContentConfig with consistent settings
    """
    config_params = {
        "system_instruction": system_prompt,
        "temperature": temperature
    }

    # Add tools if provided
    if tools:
        config_params["tools"] = tools

    return GenerateContentConfig(**config_params)
