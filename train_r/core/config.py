"""Centralized model configuration for Gemini API."""
from typing import Optional
from google.genai.types import GenerateContentConfig


def get_model_name() -> str:
    """Get the model name to use for all requests."""
    return "gemini-2.5-flash"


def get_model_config(
    system_prompt: str,
    tools: Optional[list] = None,
    temperature: float = 0
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
