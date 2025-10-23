"""Simplified Gemini client for Train-R.

This module provides a straightforward Gemini API client without abstraction layers,
following the KISS principle.
"""
import logging
from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from google import genai
from google.genai.types import GenerateContentConfig
from google.api_core import exceptions as google_exceptions

from src.utils.retry import retry_with_backoff

logger = logging.getLogger('train-r')


class FinishReason(Enum):
    """Standardized finish reasons."""
    STOP = "stop"
    MAX_TOKENS = "max_tokens"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"


@dataclass
class ToolCall:
    """Tool call representation."""
    name: str
    args: dict[str, Any]
    id: Optional[str] = None


@dataclass
class LLMResponse:
    """LLM response structure.

    Attributes:
        text: The generated text content
        has_tool_calls: Whether the response contains tool/function calls
        tool_calls: List of tool calls if any
        raw_response: Gemini raw response object
        finish_reason: Why the generation stopped
        usage: Token usage information if available
    """
    text: str
    has_tool_calls: bool = False
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw_response: Optional[Any] = None
    finish_reason: FinishReason = FinishReason.STOP
    usage: Optional[dict[str, int]] = None


@dataclass
class LLMConfig:
    """LLM generation configuration.

    Attributes:
        model: Model identifier (e.g., "gemini-2.5-flash")
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
        system_instruction: System prompt/instruction
        tools: List of available tools/functions for function calling
        max_tokens: Maximum tokens to generate
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
    """
    model: str
    temperature: float = 0.0
    system_instruction: Optional[str] = None
    tools: Optional[list] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None


class GeminiClient:
    """Google Gemini API client.

    Simple, focused client for interacting with Gemini API.
    Handles response parsing, retries, and tool calling.

    Attributes:
        client: Initialized Gemini API client
        api_key: API key for authentication
    """

    def __init__(self, api_key: str):
        """Initialize Gemini client.

        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        logger.info("GeminiClient initialized")

    def generate(
        self,
        prompt: str | list,
        config: LLMConfig
    ) -> LLMResponse:
        """Generate completion using Gemini.

        Args:
            prompt: Single prompt string or conversation history
            config: Generation configuration

        Returns:
            LLM response

        Raises:
            Exception: On API errors or validation failures
        """
        # Convert LLMConfig to Gemini-specific config
        gemini_config = self._build_gemini_config(config)

        # Define the API call function for retry wrapper
        def make_api_call() -> LLMResponse:
            response = self.client.models.generate_content(
                model=config.model,
                contents=prompt,
                config=gemini_config
            )
            return self.parse_response(response)

        # Execute with retry logic
        return retry_with_backoff(
            func=make_api_call,
            exception_types=(google_exceptions.GoogleAPIError,),
            operation_name="Gemini API call"
        )

    def parse_response(self, raw_response: Any) -> LLMResponse:
        """Parse Gemini response into standardized format.

        Gemini responses have a complex nested structure:
        response.candidates[0].content.parts[...]
        where parts can contain text or function_call

        Args:
            raw_response: Gemini API response object

        Returns:
            Standardized LLM response
        """
        # Check for candidates
        if not hasattr(raw_response, 'candidates') or not raw_response.candidates:
            return LLMResponse(
                text="",
                raw_response=raw_response,
                finish_reason=FinishReason.ERROR
            )

        candidate = raw_response.candidates[0]

        # Check for content
        if not hasattr(candidate, 'content') or not candidate.content:
            return LLMResponse(
                text="",
                raw_response=raw_response,
                finish_reason=FinishReason.ERROR
            )

        # Extract text and tool calls from parts
        text_parts = []
        tool_calls = []

        for part in candidate.content.parts:
            # Extract text
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)

            # Extract tool calls
            if hasattr(part, 'function_call') and part.function_call:
                fc = part.function_call
                tool_calls.append(ToolCall(
                    name=fc.name,
                    args=dict(fc.args) if hasattr(fc, 'args') else {},
                    id=fc.id if hasattr(fc, 'id') else None
                ))

        # Determine finish reason
        finish_reason = FinishReason.STOP
        if tool_calls:
            finish_reason = FinishReason.TOOL_CALLS
        elif hasattr(candidate, 'finish_reason'):
            # Map Gemini finish reasons to standard
            gemini_reason = str(candidate.finish_reason).lower()
            if 'length' in gemini_reason or 'max' in gemini_reason:
                finish_reason = FinishReason.MAX_TOKENS
            elif 'safety' in gemini_reason or 'filter' in gemini_reason:
                finish_reason = FinishReason.CONTENT_FILTER

        # Extract usage information if available
        usage = None
        if hasattr(raw_response, 'usage_metadata'):
            usage = {
                "prompt_tokens": getattr(raw_response.usage_metadata, 'prompt_token_count', 0),
                "completion_tokens": getattr(raw_response.usage_metadata, 'candidates_token_count', 0),
                "total_tokens": getattr(raw_response.usage_metadata, 'total_token_count', 0),
            }

        return LLMResponse(
            text="\n".join(text_parts) if text_parts else "",
            has_tool_calls=len(tool_calls) > 0,
            tool_calls=tool_calls,
            raw_response=raw_response,
            finish_reason=finish_reason,
            usage=usage
        )

    def _build_gemini_config(self, config: LLMConfig) -> GenerateContentConfig:
        """Convert LLMConfig to Gemini-specific configuration.

        Args:
            config: Standardized LLM config

        Returns:
            Gemini-specific config object
        """
        config_params = {
            "temperature": config.temperature
        }

        # Add system instruction if provided
        if config.system_instruction:
            config_params["system_instruction"] = config.system_instruction

        # Add tools if provided
        if config.tools:
            config_params["tools"] = config.tools

        # Add optional parameters
        if config.max_tokens:
            config_params["max_output_tokens"] = config.max_tokens
        if config.top_p:
            config_params["top_p"] = config.top_p
        if config.top_k:
            config_params["top_k"] = config.top_k

        return GenerateContentConfig(**config_params)
