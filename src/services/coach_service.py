"""Cycling coach conversation service using LLM client abstraction.

This service manages multi-turn conversations with tool calling support,
providing the core functionality for the Train-R cycling coach.
Includes workout generation capabilities.
"""
import logging
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Any, TYPE_CHECKING

from src.models.llm_client import LLMClient
from src.config import AppConfig
from src.utils.conversation import ConversationManager
from src.tools.loader import load_tools, get_tool_names
from src.tools.handler import handle_tool_call

logger = logging.getLogger('train-r')


class CoachService:
    """Service for managing cycling coach conversations with tool support.

    This service manages multi-turn conversations with the LLM API,
    handling tool calling, response parsing, and workout generation.

    Attributes:
        llm_client: LLM client for generating responses
        config: Application configuration
        conversation: Conversation history manager
        system_prompt: System instruction for the coach
        workout_prompt_template: System prompt for workout generation
        tools: Available tools for function calling
        tool_names: List of tool names for logging
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

        # Load system prompt
        self.system_prompt = self._load_prompt("prompts/system_prompt.txt")

        # Load workout generator prompt
        self.workout_prompt_template = self._load_prompt("prompts/workout_generator_prompt.txt")

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
                            self
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

    def generate_workout(
        self,
        client_ftp: int,
        workout_duration: int,
        workout_type: str
    ) -> str:
        """Generate a ZWO workout file using LLM.

        Args:
            client_ftp: Client's FTP in watts
            workout_duration: Duration in seconds
            workout_type: Type of workout (e.g., "Sweet Spot", "Threshold")

        Returns:
            ZWO file content as string

        Raises:
            Exception: If workout generation fails
            ValueError: If generated workout is invalid
        """
        # Build user prompt with parameters
        user_prompt = f"""Generate a workout with the following parameters:

FTP: {client_ftp}W
Duration: {workout_duration} seconds ({workout_duration // 60} minutes)
Type: {workout_type}

Return ONLY the ZWO XML file content, nothing else."""

        logger.info(f"Generating {workout_type} workout (FTP: {client_ftp}W, Duration: {workout_duration}s)")

        # Build messages with system instruction and user prompt
        messages = [
            {"role": "system", "content": self.workout_prompt_template},
            {"role": "user", "content": user_prompt}
        ]

        # Generate using LLM client
        response = self.llm_client.generate(
            messages=messages,
            model=self.config.model_name,
            temperature=self.config.temperature,
            reasoning_effort=self.config.reasoning_effort
        )

        # Extract and validate ZWO content
        zwo_content = response.choices[0].message.content.strip()

        if not self._validate_zwo(zwo_content):
            raise ValueError("Generated workout is missing required XML structure")

        logger.info("Workout generated successfully")
        return zwo_content

    def save_workout(self, zwo_content: str, workout_type: str) -> str:
        """Save ZWO workout to file.

        Args:
            zwo_content: ZWO file content
            workout_type: Type of workout for filename

        Returns:
            Path to saved file as string
        """
        # Create directory if needed
        output_dir = self.config.workouts_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize workout type for filename
        safe_type = re.sub(r'[^a-z0-9]+', '_', workout_type.lower()).strip('_')

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_type}_{timestamp}.zwo"
        filepath = output_dir / filename

        # Save file
        with open(filepath, 'w') as f:
            f.write(zwo_content)

        logger.info(f"Workout saved to: {filepath}")
        return str(filepath)

    def _validate_zwo(self, zwo_content: str) -> bool:
        """Validate ZWO file content.

        Args:
            zwo_content: ZWO file content to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation - ensure it has workout_file tags
        return "<workout_file>" in zwo_content and "</workout_file>" in zwo_content

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation.clear()
        logger.info("Conversation reset")
