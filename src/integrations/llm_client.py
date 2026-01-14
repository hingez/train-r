"""OpenAI-compatible LLM client for Train-R.

This module provides an OpenAI library-based client that can connect to
OpenAI-compatible endpoints (currently configured for Gemini), following the KISS principle.
Supports LangSmith tracing for observability.
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional, Any
from openai import OpenAI
from openai.types.chat import ChatCompletion

from src.utils.retry import retry_with_backoff

logger = logging.getLogger('train-r')


class LLMClient:
    """OpenAI-compatible LLM client.

    Simple, focused client for interacting with LLM providers via OpenAI library.
    Handles retries and provides a consistent interface. Supports LangSmith tracing
    for observability when enabled.

    Attributes:
        client: Initialized OpenAI client (potentially wrapped with LangSmith)
        api_key: API key for authentication
        base_url: LLM provider's OpenAI-compatible endpoint
        messages_log_path: Path to JSON file for logging messages sent to LLM
        langsmith_enabled: Whether LangSmith tracing is active
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        messages_log_path: Optional[Path] = None,
        langsmith_tracing_enabled: bool = False,
        langsmith_api_key: Optional[str] = None,
        langsmith_project: Optional[str] = None
    ):
        """Initialize LLM client.

        Args:
            api_key: LLM provider API key
            base_url: Base URL for LLM API endpoint
            messages_log_path: Optional path to JSON file for logging LLM messages
            langsmith_tracing_enabled: Enable LangSmith tracing
            langsmith_api_key: API key for LangSmith (optional)
            langsmith_project: Project name for LangSmith (optional)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.langsmith_enabled = False

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key, base_url=base_url)

        # Wrap with LangSmith if enabled and configured
        if langsmith_tracing_enabled and langsmith_api_key:
            try:
                from langsmith.wrappers import wrap_openai

                # Set LangSmith environment variables
                os.environ["LANGSMITH_TRACING"] = "true"
                os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
                if langsmith_project:
                    os.environ["LANGSMITH_PROJECT"] = langsmith_project

                # Wrap the client
                self.client = wrap_openai(client)
                self.langsmith_enabled = True
                logger.info(f"LangSmith tracing enabled for project: {langsmith_project or 'default'}")
            except ImportError:
                logger.warning("LangSmith package not installed. Tracing disabled.")
                self.client = client
            except Exception as e:
                logger.warning(f"Failed to enable LangSmith tracing: {e}")
                self.client = client
        else:
            self.client = client
            if langsmith_tracing_enabled:
                logger.info("LangSmith tracing requested but API key not provided")

        # Set up messages log path (defaults to logs/llm_messages.json)
        if messages_log_path is None:
            from src.config import PROJECT_ROOT
            self.messages_log_path = PROJECT_ROOT / "logs" / "llm_messages.json"
        else:
            self.messages_log_path = messages_log_path

        logger.info(f"LLMClient initialized with endpoint: {base_url}")
        logger.info(f"LLM messages will be logged to: {self.messages_log_path}")

    def _write_messages_to_log(self, messages: list[dict[str, Any]], params: dict[str, Any]):
        """Write messages and parameters to JSON log file.

        Args:
            messages: List of message dictionaries being sent to LLM
            params: Full parameters dict being sent to LLM API
        """
        try:
            log_data = {
                "timestamp": time.time(),
                "messages": messages,
                "parameters": {
                    "model": params.get("model"),
                    "temperature": params.get("temperature"),
                    "tools": params.get("tools"),
                    "tool_choice": params.get("tool_choice"),
                    "max_tokens": params.get("max_tokens"),
                    "top_p": params.get("top_p"),
                    "reasoning_effort": params.get("reasoning_effort")
                }
            }

            # Write to file (overwrite)
            with open(self.messages_log_path, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)

        except Exception as e:
            # Don't fail the API call if logging fails
            logger.warning(f"Failed to write messages to log file: {e}")

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
        request_id: Optional[str] = None,
        run_name: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> ChatCompletion:
        """Generate completion using OpenAI library.

        Args:
            messages: List of message dictionaries with role and content
            model: Model identifier
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            tools: List of available tools/functions for function calling
            tool_choice: How to use tools ("auto", "required", "none")
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            reasoning_effort: Thinking control ("low", "medium", "high", "none")
            request_id: Optional request ID for logging correlation
            run_name: Optional name for this LLM run in LangSmith (e.g., "CoachAgent", "WorkoutGenerator")
            session_id: Optional session ID for LangSmith thread grouping
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

        # Write messages to log file
        self._write_messages_to_log(messages, params)

        # Log request details
        req_prefix = f"[req={request_id}] " if request_id else ""
        logger.info(f"{req_prefix}LLM_REQUEST model={model} temp={temperature} messages={len(messages)} tools={len(tools or [])}")

        # Build LangSmith metadata if tracing enabled
        if self.langsmith_enabled:
            try:
                from langsmith import traceable

                # Build langsmith_extra with thread_id for conversation grouping
                # thread_id must be at top level (not in metadata) for LangSmith UI grouping
                langsmith_extra = {}
                if session_id:
                    langsmith_extra["thread_id"] = session_id
                if run_name:
                    langsmith_extra["name"] = run_name

                # Wrap the API call with traceable decorator
                @traceable(run_type="llm", **langsmith_extra)
                def make_traced_api_call() -> ChatCompletion:
                    return self.client.chat.completions.create(**params)

                make_api_call = make_traced_api_call
            except ImportError:
                # Fall back to non-traced call if traceable not available
                def make_api_call() -> ChatCompletion:
                    return self.client.chat.completions.create(**params)
        else:
            # Define the API call function for retry wrapper
            def make_api_call() -> ChatCompletion:
                return self.client.chat.completions.create(**params)

        # Execute with retry logic and timing
        start_time = time.time()

        try:
            result = retry_with_backoff(
                func=make_api_call,
                exception_types=(Exception,),  # OpenAI library raises various exceptions
                operation_name="LLM API call"
            )

            # Log response details
            duration_ms = int((time.time() - start_time) * 1000)
            usage = result.usage
            finish_reason = result.choices[0].finish_reason

            logger.info(f"{req_prefix}LLM_RESPONSE duration={duration_ms}ms tokens={usage.total_tokens} "
                       f"(prompt={usage.prompt_tokens}, completion={usage.completion_tokens}) "
                       f"finish={finish_reason}")

            # Log tool calls if present
            if result.choices[0].message.tool_calls:
                tool_names = [tc.function.name for tc in result.choices[0].message.tool_calls]
                logger.info(f"{req_prefix}LLM_TOOL_CALLS count={len(tool_names)} tools={tool_names}")

            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"{req_prefix}LLM_ERROR duration={duration_ms}ms error={type(e).__name__} msg={str(e)}")
            raise
