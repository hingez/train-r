"""OpenAI-compatible LLM client for Train-R using Gemini.

This module provides an OpenAI library-based client that connects to Gemini's
OpenAI-compatible endpoint, following the KISS principle.
"""
import logging
from typing import Optional, Any
from openai import OpenAI
from openai.types.chat import ChatCompletion

from src.utils.retry import retry_with_backoff

logger = logging.getLogger('train-r')


class LLMClient:
    """OpenAI-compatible LLM client using Gemini endpoint.

    Simple, focused client for interacting with Gemini via OpenAI library.
    Handles retries and provides a consistent interface.

    Attributes:
        client: Initialized OpenAI client pointed at Gemini endpoint
        api_key: API key for authentication
        base_url: Gemini OpenAI-compatible endpoint
    """

    def __init__(self, api_key: str):
        """Initialize LLM client.

        Args:
            api_key: Gemini API key
        """
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url
        )
        logger.info("LLMClient initialized with Gemini endpoint")

    def generate(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.0,
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: str = "auto",
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        reasoning_effort: Optional[str] = None,
        **kwargs
    ) -> ChatCompletion:
        """Generate completion using OpenAI library with Gemini.

        Args:
            messages: List of message dictionaries with role and content
            model: Model identifier (e.g., "gemini-2.5-flash")
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            tools: List of available tools/functions for function calling
            tool_choice: How to use tools ("auto", "required", "none")
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            reasoning_effort: Thinking control ("low", "medium", "high", "none")
            **kwargs: Additional parameters to pass to the API

        Returns:
            OpenAI ChatCompletion object

        Raises:
            Exception: On API errors
        """
        # Build request parameters
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        # Add tools if provided
        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice

        # Add optional parameters
        if max_tokens:
            params["max_tokens"] = max_tokens
        if top_p:
            params["top_p"] = top_p
        if reasoning_effort:
            params["reasoning_effort"] = reasoning_effort

        # Add any extra kwargs
        params.update(kwargs)

        # Define the API call function for retry wrapper
        def make_api_call() -> ChatCompletion:
            return self.client.chat.completions.create(**params)

        # Execute with retry logic
        return retry_with_backoff(
            func=make_api_call,
            exception_types=(Exception,),  # OpenAI library raises various exceptions
            operation_name="LLM API call"
        )
