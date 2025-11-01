"""Conversation history management for multi-turn interactions."""
from typing import Any
from openai.types.chat import ChatCompletion
import json


class ConversationManager:
    """Manage conversation history for OpenAI-compatible API calls."""

    def __init__(self, system_instruction: str = None):
        """Initialize conversation history.

        Args:
            system_instruction: Optional system instruction to prepend
        """
        self.history = []
        if system_instruction:
            self.history.append({
                "role": "system",
                "content": system_instruction
            })

    def add_user_message(self, text: str):
        """Add a user message to the conversation history.

        Args:
            text: User's message text
        """
        self.history.append({
            "role": "user",
            "content": text
        })

    def add_model_response(self, response: ChatCompletion):
        """Add a model response to the conversation history.

        Args:
            response: ChatCompletion object from OpenAI-compatible API
        """
        if not response.choices:
            return

        message = response.choices[0].message

        # Build the message to add to history
        history_message = {
            "role": "assistant"
        }

        # Add content if present
        if message.content:
            history_message["content"] = message.content

        # Add tool calls if present
        if message.tool_calls:
            history_message["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]

        self.history.append(history_message)

    def add_tool_response(self, tool_call_id: str, tool_name: str, result: dict):
        """Add a tool response to the conversation history.

        Args:
            tool_call_id: ID of the tool call
            tool_name: Name of the tool that was called
            result: Result dictionary from tool execution
        """
        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": json.dumps(result)
        })

    def get_history(self) -> list:
        """Get the conversation history.

        Returns:
            List of conversation turns formatted for OpenAI API
        """
        return self.history

    def clear(self):
        """Clear the conversation history (keeping system message if present)."""
        system_messages = [msg for msg in self.history if msg.get("role") == "system"]
        self.history = system_messages
