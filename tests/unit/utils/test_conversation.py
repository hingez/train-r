"""Tests for ConversationManager utility."""
import json
import pytest
from unittest.mock import Mock

from src.utils.conversation import ConversationManager


class TestConversationManagerInit:
    """Test ConversationManager initialization."""

    def test_init_without_system_instruction(self):
        """Should initialize with empty history."""
        manager = ConversationManager()
        assert manager.history == []

    def test_init_with_system_instruction(self):
        """Should initialize with system message in history."""
        manager = ConversationManager(system_instruction="You are a coach.")

        assert len(manager.history) == 1
        assert manager.history[0] == {
            "role": "system",
            "content": "You are a coach."
        }


class TestAddUserMessage:
    """Test adding user messages."""

    def test_adds_user_message_to_history(self):
        """Should add user message with correct format."""
        manager = ConversationManager()
        manager.add_user_message("Hello, coach!")

        assert len(manager.history) == 1
        assert manager.history[0] == {
            "role": "user",
            "content": "Hello, coach!"
        }

    def test_adds_multiple_user_messages(self):
        """Should append multiple user messages."""
        manager = ConversationManager()
        manager.add_user_message("First message")
        manager.add_user_message("Second message")

        assert len(manager.history) == 2
        assert manager.history[0]["content"] == "First message"
        assert manager.history[1]["content"] == "Second message"

    def test_preserves_order_with_system_message(self):
        """Should maintain order with system message first."""
        manager = ConversationManager(system_instruction="System prompt")
        manager.add_user_message("User message")

        assert len(manager.history) == 2
        assert manager.history[0]["role"] == "system"
        assert manager.history[1]["role"] == "user"


class TestAddModelResponse:
    """Test adding model responses."""

    def test_adds_text_response(self, mock_llm_response):
        """Should add assistant message with text content."""
        manager = ConversationManager()
        manager.add_model_response(mock_llm_response)

        assert len(manager.history) == 1
        assert manager.history[0]["role"] == "assistant"
        assert manager.history[0]["content"] == "Test response from LLM"

    def test_handles_empty_choices(self):
        """Should handle response with no choices."""
        manager = ConversationManager()
        response = Mock()
        response.choices = []

        manager.add_model_response(response)
        assert len(manager.history) == 0

    def test_adds_response_with_tool_calls(self, mock_llm_response_with_tool_call):
        """Should add assistant message with tool calls."""
        manager = ConversationManager()
        manager.add_model_response(mock_llm_response_with_tool_call)

        assert len(manager.history) == 1
        msg = manager.history[0]
        assert msg["role"] == "assistant"
        assert "tool_calls" in msg
        assert len(msg["tool_calls"]) == 1
        assert msg["tool_calls"][0]["id"] == "call_123"
        assert msg["tool_calls"][0]["type"] == "function"
        assert msg["tool_calls"][0]["function"]["name"] == "create_one_off_workout"

    def test_tool_call_arguments_preserved(self, mock_llm_response_with_tool_call):
        """Should preserve tool call arguments as JSON string."""
        manager = ConversationManager()
        manager.add_model_response(mock_llm_response_with_tool_call)

        args_str = manager.history[0]["tool_calls"][0]["function"]["arguments"]
        args = json.loads(args_str)

        assert args["client_ftp"] == 250
        assert args["workout_duration"] == 3600
        assert args["workout_type"] == "Sweet Spot"

    def test_handles_response_without_content(self):
        """Should handle response with tool calls but no text content."""
        manager = ConversationManager()
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None
        response.choices[0].message.tool_calls = None

        manager.add_model_response(response)

        assert len(manager.history) == 1
        assert "content" not in manager.history[0]


class TestAddToolResponse:
    """Test adding tool responses."""

    def test_adds_tool_response_with_correct_format(self):
        """Should add tool response with all required fields."""
        manager = ConversationManager()
        result = {"success": True, "data": "workout created"}

        manager.add_tool_response(
            tool_call_id="call_123",
            tool_name="create_one_off_workout",
            result=result
        )

        assert len(manager.history) == 1
        msg = manager.history[0]
        assert msg["role"] == "tool"
        assert msg["tool_call_id"] == "call_123"
        assert msg["name"] == "create_one_off_workout"
        assert json.loads(msg["content"]) == result

    def test_serializes_result_to_json(self):
        """Should serialize result dict to JSON string."""
        manager = ConversationManager()
        result = {"nested": {"data": [1, 2, 3]}}

        manager.add_tool_response("id", "tool", result)

        content = json.loads(manager.history[0]["content"])
        assert content == result

    def test_adds_multiple_tool_responses(self):
        """Should handle multiple tool responses in sequence."""
        manager = ConversationManager()

        manager.add_tool_response("call_1", "tool_a", {"result": "a"})
        manager.add_tool_response("call_2", "tool_b", {"result": "b"})

        assert len(manager.history) == 2
        assert manager.history[0]["tool_call_id"] == "call_1"
        assert manager.history[1]["tool_call_id"] == "call_2"


class TestGetUserWorkoutHistory:
    """Test getting conversation history."""

    def test_returns_full_history(self):
        """Should return complete conversation history."""
        manager = ConversationManager(system_instruction="System")
        manager.add_user_message("User message")

        history = manager.get_user_workout_history()

        assert len(history) == 2
        assert history[0]["role"] == "system"
        assert history[1]["role"] == "user"

    def test_returns_same_list_object(self):
        """Should return reference to internal history list."""
        manager = ConversationManager()
        history = manager.get_user_workout_history()

        assert history is manager.history

    def test_empty_history_returns_empty_list(self):
        """Should return empty list for new manager without system prompt."""
        manager = ConversationManager()
        assert manager.get_user_workout_history() == []


class TestClear:
    """Test clearing conversation history."""

    def test_clear_preserves_system_messages(self):
        """Should keep system messages when clearing."""
        manager = ConversationManager(system_instruction="System prompt")
        manager.add_user_message("User message")
        manager.add_tool_response("id", "tool", {})

        manager.clear()

        assert len(manager.history) == 1
        assert manager.history[0]["role"] == "system"
        assert manager.history[0]["content"] == "System prompt"

    def test_clear_removes_non_system_messages(self):
        """Should remove user, assistant, and tool messages."""
        manager = ConversationManager(system_instruction="System")
        manager.add_user_message("User")

        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = "Assistant"
        response.choices[0].message.tool_calls = None
        manager.add_model_response(response)

        manager.add_tool_response("id", "tool", {})

        # Should have 4 messages before clear
        assert len(manager.history) == 4

        manager.clear()

        # Only system message remains
        assert len(manager.history) == 1
        assert manager.history[0]["role"] == "system"

    def test_clear_without_system_message(self):
        """Should result in empty history when no system message exists."""
        manager = ConversationManager()
        manager.add_user_message("Message 1")
        manager.add_user_message("Message 2")

        manager.clear()

        assert manager.history == []


class TestConversationFlow:
    """Integration tests for realistic conversation flows."""

    def test_complete_conversation_with_tool_call(self):
        """Should handle a complete conversation with tool calling."""
        manager = ConversationManager(system_instruction="You are a cycling coach.")

        # User asks for workout
        manager.add_user_message("Create a 1 hour sweet spot workout")

        # Model responds with tool call
        tool_response = Mock()
        tool_response.choices = [Mock()]
        tool_response.choices[0].message = Mock()
        tool_response.choices[0].message.content = None
        tool_call = Mock()
        tool_call.id = "call_abc"
        tool_call.function = Mock()
        tool_call.function.name = "create_one_off_workout"
        tool_call.function.arguments = '{"client_ftp": 250, "workout_duration": 3600}'
        tool_response.choices[0].message.tool_calls = [tool_call]
        manager.add_model_response(tool_response)

        # Tool executes
        manager.add_tool_response("call_abc", "create_one_off_workout", {
            "success": True,
            "workout_file": "/path/to/workout.zwo"
        })

        # Model gives final response
        final_response = Mock()
        final_response.choices = [Mock()]
        final_response.choices[0].message = Mock()
        final_response.choices[0].message.content = "I've created your workout!"
        final_response.choices[0].message.tool_calls = None
        manager.add_model_response(final_response)

        # Verify conversation structure
        history = manager.get_user_workout_history()
        assert len(history) == 5

        assert history[0]["role"] == "system"
        assert history[1]["role"] == "user"
        assert history[2]["role"] == "assistant"
        assert "tool_calls" in history[2]
        assert history[3]["role"] == "tool"
        assert history[4]["role"] == "assistant"
        assert history[4]["content"] == "I've created your workout!"
