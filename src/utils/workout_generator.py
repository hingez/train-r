"""Workout generation and file management utility.

This module handles ZWO workout file generation using LLM and file I/O operations.
"""
import logging
import re
from datetime import datetime
from pathlib import Path

from src.integrations.llm_client import LLMClient
from src.config import AppConfig

logger = logging.getLogger('train-r')


class WorkoutGenerator:
    """Handles workout generation and file operations.

    Attributes:
        llm_client: LLM client for generating workout content
        config: Application configuration
        workout_prompt_template: System prompt for workout generation
    """

    def __init__(self, llm_client: LLMClient, config: AppConfig):
        """Initialize workout generator.

        Args:
            llm_client: Initialized LLM client
            config: Application configuration
        """
        self.llm_client = llm_client
        self.config = config

        # Load workout generator prompt
        self.workout_prompt_template = self._load_prompt("prompts/workout_generator_prompt.txt")

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
