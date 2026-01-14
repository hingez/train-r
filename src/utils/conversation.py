"""Conversation history management for LLM interactions."""
import json
import uuid
from typing import Optional
from openai.types.chat import ChatCompletion


class ConversationManager:
    """Manages conversation history for LLM interactions.

    Maintains conversation history in OpenAI chat format with support for
    system messages, user messages, assistant messages, and tool calls.
    Includes session tracking for LangSmith thread grouping.

    Attributes:
        history: List of conversation messages
        session_id: Unique identifier for this conversation session
    """

    def __init__(self, system_instruction: Optional[str] = None, session_id: Optional[str] = None):
        """Initialize conversation manager.

        Args:
            system_instruction: Optional system prompt to start conversation
            session_id: Optional session ID for LangSmith threading (auto-generated if not provided)
        """
        self.history = []
        self.session_id = session_id or str(uuid.uuid4())

        if system_instruction:
            self.history.append({"role": "system", "content": system_instruction})

    def add_user_message(self, content: str):
        """Add a user message to history.

        Args:
            content: User message content
        """
        self.history.append({"role": "user", "content": content})

    def add_model_response(self, response: ChatCompletion):
        """Add a model response to the conversation history.

        Args:
            response: ChatCompletion object from OpenAI-compatible API
        """
        if not response.choices:
            return

        message = response.choices[0].message

        # Convert to dict using model_dump to preserve standard fields
        history_message = message.model_dump(exclude_none=True)

        # Explicitly handle extra_content for Gemini thought signatures
        # This is required for Gemini 3 models to enable function calling
        
        # Check for top-level extra_content (text-only thought signatures)
        if hasattr(message, 'model_extra') and message.model_extra and 'extra_content' in message.model_extra:
            history_message['extra_content'] = message.model_extra['extra_content']
        elif hasattr(message, 'extra_content'):
             history_message['extra_content'] = message.extra_content

        # Check for tool_call level extra_content
        if message.tool_calls and 'tool_calls' in history_message:
            for i, tc in enumerate(message.tool_calls):
                extra_content = None
                if hasattr(tc, 'model_extra') and tc.model_extra and 'extra_content' in tc.model_extra:
                    extra_content = tc.model_extra['extra_content']
                elif hasattr(tc, 'extra_content'):
                    extra_content = tc.extra_content
                
                if extra_content:
                    history_message['tool_calls'][i]['extra_content'] = extra_content

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

    def get_user_workout_history(self) -> list[dict]:
        """Get conversation history.

        Returns:
            List of conversation messages
        """
        return self.history

    def clear(self):
        """Clear conversation history (keeping system messages)."""
        system_messages = [msg for msg in self.history if msg.get("role") == "system"]
        self.history = system_messages
