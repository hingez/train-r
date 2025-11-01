"""Cycling coach conversation service using LLM client abstraction.

This service manages multi-turn conversations with tool calling support,
providing the core functionality for the Train-R cycling coach.
"""
import logging
from pathlib import Path
from typing import Optional, Callable, Any, TYPE_CHECKING
import json

from src.models.llm_client import LLMClient
from src.config import AppConfig
from src.utils.conversation import ConversationManager
from src.tools.loader import load_tools, get_tool_names
from src.tools.handler import handle_tool_call

if TYPE_CHECKING:
    from src.services.workout_service import WorkoutService

logger = logging.getLogger('train-r')


class CoachService:
    """Service for managing cycling coach conversations with tool support.

    This service manages multi-turn conversations with the LLM API,
    handling tool calling and response parsing.

    Attributes:
        llm_client: LLM client for generating responses
        config: Application configuration
        workout_service: Workout generation service
        conversation: Conversation history manager
        system_prompt: System instruction for the coach
        tools: Available tools for function calling
        tool_names: List of tool names for logging
    """

    def __init__(
        self,
        llm_client: LLMClient,
        config: AppConfig,
        workout_service: "WorkoutService"
    ):
        """Initialize coach service.

        Args:
            llm_client: Initialized LLM client
            config: Application configuration
            workout_service: Workout generation service
        """
        self.llm_client = llm_client
        self.config = config
        self.workout_service = workout_service

        # Load system prompt
        self.system_prompt = self._load_prompt("prompts/system_prompt.txt")

        # Initialize conversation with system prompt
        self.conversation = ConversationManager(system_instruction=self.system_prompt)

        # Load tools
        self.tools = load_tools(str(config.tools_dir))
        self.tool_names = get_tool_names(self.tools)

        logger.info(f"CoachService initialized with {len(self.tool_names)} tools: {', '.join(self.tool_names)}")

    def _load_prompt(self, prompt_path: str) -> str:
        """Load system prompt from file.

        Args:
            prompt_path: Path to prompt file relative to project root

        Returns:
            Prompt content
        """
        full_path = self.config.project_root / prompt_path
        with open(full_path, 'r') as f:
            return f.read()

    async def process_message(
        self,
        user_message: str,
        on_tool_call: Optional[Callable[[str, dict], Any]] = None,
        on_tool_result: Optional[Callable[[str, dict, bool], Any]] = None
    ) -> str:
        """Process user message and return assistant response.

        Manages the conversation flow including tool execution loop.

        Args:
            user_message: User's message text
            on_tool_call: Optional callback when tool is called (tool_name, tool_args)
            on_tool_result: Optional callback when tool completes (tool_name, result, success)

        Returns:
            Assistant's text response

        Raises:
            Exception: If API call fails
        """
        # Add user message to conversation
        self.conversation.add_user_message(user_message)
        logger.info(f"USER: {user_message}")

        try:
            # Generate response
            response = self.llm_client.generate(
                messages=self.conversation.get_history(),
                model=self.config.model_name,
                temperature=self.config.temperature,
                tools=self.tools,
                tool_choice="auto",
                reasoning_effort=self.config.reasoning_effort
            )

            # Handle tool calls in a loop
            iteration = 0
            max_iterations = 10

            while response.choices[0].message.tool_calls and iteration < max_iterations:
                iteration += 1

                # Add model response with tool calls to history
                self.conversation.add_model_response(response)

                # Execute each tool call
                for tool_call in response.choices[0].message.tool_calls:
                    # Parse arguments from JSON string
                    args = json.loads(tool_call.function.arguments)
                    logger.info(f"TOOL_CALL: {tool_call.function.name}")

                    # Notify via callback if provided
                    if on_tool_call:
                        await on_tool_call(tool_call.function.name, args)

                    # Execute tool
                    try:
                        # Create a simple object to pass to handle_tool_call
                        class ToolCallObj:
                            def __init__(self, name, args):
                                self.name = name
                                self.args = args

                        result = handle_tool_call(
                            ToolCallObj(tool_call.function.name, args),
                            self.config,
                            self.workout_service
                        )
                        success = result.get("success", True)

                        # Add tool response to conversation
                        self.conversation.add_tool_response(
                            tool_call.id,
                            tool_call.function.name,
                            result
                        )

                        # Notify via callback if provided
                        if on_tool_result:
                            await on_tool_result(tool_call.function.name, result, success)

                    except Exception as e:
                        logger.error(f"Tool execution error: {e}", exc_info=True)
                        error_result = {"success": False, "error": str(e)}

                        self.conversation.add_tool_response(
                            tool_call.id,
                            tool_call.function.name,
                            error_result
                        )

                        if on_tool_result:
                            await on_tool_result(tool_call.function.name, error_result, False)

                # Generate again with tool results
                response = self.llm_client.generate(
                    messages=self.conversation.get_history(),
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    tools=self.tools,
                    tool_choice="auto",
                    reasoning_effort=self.config.reasoning_effort
                )

            if iteration >= max_iterations:
                logger.warning(f"Tool calling exceeded max iterations ({max_iterations})")

            # Add final model response to history
            self.conversation.add_model_response(response)

            # Extract and return text response
            text_response = response.choices[0].message.content or ""
            logger.info(f"ASSISTANT: {text_response}")

            return text_response if text_response else "(No response)"

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            raise Exception(f"Failed to process message: {str(e)}")

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation.clear()
        logger.info("Conversation reset")
