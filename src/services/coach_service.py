"""Cycling coach conversation service using LLM client abstraction.

This service manages multi-turn conversations with tool calling support,
providing the core functionality for the Train-R cycling coach.
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any

from src.integrations.llm_client import LLMClient
from src.config import AppConfig
from src.utils.conversation import ConversationManager
from src.utils.workout_generator import WorkoutGenerator
from src.utils.performance_history_formatter import format_performance_history
from src.tools.loader import load_tools, get_tool_names, load_tool_executors

logger = logging.getLogger('train-r')


class CoachService:
    """Service for managing cycling coach conversations with tool support.

    This service orchestrates multi-turn conversations with the LLM API,
    coordinating between conversation management, tool execution, and workout generation.

    Attributes:
        llm_client: LLM client for generating responses
        config: Application configuration
        conversation: Conversation history manager
        workout_generator: Workout generation utility
        tools: Available tools for function calling
        tool_names: List of tool names for logging
        tool_executors: Dict mapping tool names to their execute functions
    """

    def __init__(
        self,
        llm_client: LLMClient,
        config: AppConfig
    ):
        """Initialize coach service.

        Args:
            llm_client: Initialized LLM client
            config: Application configuration
        """
        self.llm_client = llm_client
        self.config = config
        self.current_session_id: Optional[str] = None  # Set during process_message for tool access

        # Load system prompt template
        system_prompt_template = self._load_prompt("prompts/system_prompt.txt")

        from datetime import timezone
        date_time = datetime.now(timezone.utc).isoformat()

        # Load and format performance history
        performance_history = self._load_performance_history()

        # Populate template variables
        system_prompt = system_prompt_template.format(
            athleteWorkoutContext=performance_history,
            date_time=date_time
        )

        # Initialize conversation manager
        self.conversation = ConversationManager(system_instruction=system_prompt)

        # Initialize workout generator
        self.workout_generator = WorkoutGenerator(llm_client, config)

        # Load tools and their executors
        self.tools = load_tools(str(config.tools_dir))
        self.tool_names = get_tool_names(self.tools)
        self.tool_executors = load_tool_executors(str(config.tools_dir))

        logger.info(f"CoachService initialized with {len(self.tool_names)} tools: {', '.join(self.tool_names)}")

    def _load_prompt(self, prompt_path: str) -> str:
        """Load prompt from file.

        Args:
            prompt_path: Path to prompt file relative to project root

        Returns:
            Prompt content
        """
        full_path = self.config.project_root / prompt_path
        with open(full_path, 'r') as f:
            return f.read()

    def _load_performance_history(self) -> str:
        """Load and format athlete performance history.

        Returns:
            Formatted performance history string
        """
        athlete_data_dir = self.config.project_root / "data" / "athlete"
        return format_performance_history(athlete_data_dir)

    async def process_message(
        self,
        user_message: str,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        on_tool_call: Optional[Callable[[str, dict], Any]] = None,
        on_tool_result: Optional[Callable[[str, dict, bool], Any]] = None
    ) -> str:
        """Process user message and return assistant response.

        Manages the conversation flow including tool execution loop.

        Args:
            user_message: User's message text
            request_id: Optional request ID for logging correlation
            session_id: Optional session ID for LangSmith thread grouping (use client_id)
            on_tool_call: Optional callback when tool is called (tool_name, tool_args)
            on_tool_result: Optional callback when tool completes (tool_name, result, success)

        Returns:
            Assistant's text response

        Raises:
            Exception: If API call fails
        """
        # Store session_id for tool access during this message processing
        self.current_session_id = session_id

        # Add user message to conversation
        self.conversation.add_user_message(user_message)

        # Log with request correlation
        req_prefix = f"[req={request_id}] " if request_id else ""
        logger.info(f"{req_prefix}USER: {user_message}")

        try:
            # Generate initial response
            response = self.llm_client.generate(
                messages=self.conversation.get_user_workout_history(),
                model=self.config.model_name,
                temperature=self.config.temperature,
                tools=self.tools,
                tool_choice="auto",
                reasoning_effort=self.config.reasoning_effort,
                request_id=request_id,
                session_id=session_id,
                run_name="CoachAgent"
            )

            # Handle tool calls in a loop
            iteration = 0

            while response.choices[0].message.tool_calls and iteration < self.config.max_tool_iterations:
                iteration += 1

                # Add model response with tool calls to history
                self.conversation.add_model_response(response)

                # Execute each tool call
                for tool_call in response.choices[0].message.tool_calls:
                    await self._execute_tool_call(
                        tool_call,
                        request_id,
                        on_tool_call,
                        on_tool_result
                    )

                # Generate next response with tool results
                try:
                    response = self.llm_client.generate(
                        messages=self.conversation.get_user_workout_history(),
                        model=self.config.model_name,
                        temperature=self.config.temperature,
                        tools=self.tools,
                        tool_choice="auto",
                        reasoning_effort=self.config.reasoning_effort,
                        request_id=request_id,
                        session_id=session_id,
                        run_name="CoachAgent"
                    )
                except Exception as e:
                    logger.warning(f"{req_prefix}Failed to generate response after tool execution: {e}")
                    # If we executed tools successfully but failed to generate a response,
                    # we should return a fallback message instead of failing the whole request.
                    return "I've completed the requested action, but I encountered an issue generating the final text response."

            if iteration >= self.config.max_tool_iterations:
                logger.warning(f"Tool calling exceeded max iterations ({self.config.max_tool_iterations})")

            # Add final model response to history
            self.conversation.add_model_response(response)

            # Extract and return text response
            text_response = response.choices[0].message.content or ""
            logger.info(f"{req_prefix}ASSISTANT: {text_response}")

            return text_response if text_response else "(No response)"

        except Exception as e:
            logger.error(f"{req_prefix}Error processing message: {e}", exc_info=True)
            raise Exception(f"Failed to process message: {str(e)}")

    async def _execute_tool_call(
        self,
        tool_call: Any,
        request_id: Optional[str] = None,
        on_tool_call: Optional[Callable] = None,
        on_tool_result: Optional[Callable] = None
    ):
        """Execute a single tool call and add result to conversation.

        Args:
            tool_call: Tool call object from LLM response
            request_id: Optional request ID for logging correlation
            on_tool_call: Optional callback when tool is called
            on_tool_result: Optional callback when tool completes
        """
        # Parse tool call details
        tool_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # Log with request correlation
        req_prefix = f"[req={request_id}] " if request_id else ""
        logger.info(f"{req_prefix}TOOL_CALL: {tool_name}")

        # Notify via callback if provided
        if on_tool_call:
            await on_tool_call(tool_name, args)

        # Execute tool
        try:
            # Get executor for this tool
            executor = self.tool_executors.get(tool_name)

            if executor:
                # Call the tool executor directly
                result = executor(args, self.config, self)
                success = result.get("success", True)
                logger.info(f"TOOL_RESULT: {json.dumps(result, indent=2)}")
            else:
                logger.warning(f"No executor found for tool: {tool_name}")
                result = {"result": "tool run successfully"}
                success = True

            # Add tool response to conversation
            self.conversation.add_tool_response(tool_call.id, tool_name, result)

            # Notify via callback if provided
            if on_tool_result:
                await on_tool_result(tool_name, result, success)

        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            error_result = {"success": False, "error": str(e)}

            self.conversation.add_tool_response(tool_call.id, tool_name, error_result)

            if on_tool_result:
                await on_tool_result(tool_name, error_result, False)

    # Delegate workout methods to workout_generator
    def generate_workout(self, client_ftp: int, workout_duration: int, workout_type: str) -> str:
        """Generate a ZWO workout file using LLM.

        Args:
            client_ftp: Client's FTP in watts
            workout_duration: Duration in seconds
            workout_type: Type of workout

        Returns:
            ZWO file content as string
        """
        return self.workout_generator.generate_workout(client_ftp, workout_duration, workout_type)

    def save_workout(self, zwo_content: str, workout_type: str) -> str:
        """Save ZWO workout to file.

        Args:
            zwo_content: ZWO file content
            workout_type: Type of workout for filename

        Returns:
            Path to saved file as string
        """
        return self.workout_generator.save_workout(zwo_content, workout_type)

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation.clear()
        logger.info("Conversation reset")
