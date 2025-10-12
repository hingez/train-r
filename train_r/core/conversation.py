"""Conversation history management for multi-turn interactions."""
from typing import Any


class ConversationManager:
    """Manage conversation history for Gemini API calls."""

    def __init__(self):
        """Initialize conversation history."""
        self.history = []

    def add_user_message(self, text: str):
        """Add a user message to the conversation history.

        Args:
            text: User's message text
        """
        self.history.append({
            "role": "user",
            "parts": [{"text": text}]
        })

    def add_model_response(self, response: Any):
        """Add a model response to the conversation history.

        Args:
            response: Model response object from Gemini
        """
        # Check if response has function calls
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                content = candidate.content

                # Add the entire model response content
                self.history.append({
                    "role": "model",
                    "parts": content.parts
                })

    def add_tool_response(self, tool_call: Any, result: dict):
        """Add a tool response to the conversation history.

        Args:
            tool_call: Tool call object from model response
            result: Result dictionary from tool execution
        """
        # Function responses are added as user role with function_response
        self.history.append({
            "role": "user",
            "parts": [{
                "function_response": {
                    "name": tool_call.name,
                    "response": result
                }
            }]
        })

    def get_history(self) -> list:
        """Get the conversation history.

        Returns:
            List of conversation turns formatted for Gemini API
        """
        return self.history

    def clear(self):
        """Clear the conversation history."""
        self.history = []
