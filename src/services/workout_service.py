"""Workout generation service using LLM client abstraction.

This service handles all workout-related operations including:
- Generating ZWO workout files using LLM
- Saving workouts to disk
- Validating workout content
"""
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.llm_client import LLMClient
from src.config import AppConfig

logger = logging.getLogger('train-r')


class WorkoutService:
    """Service for generating and managing workouts.

    Uses LLM to generate structured ZWO workout files.

    Attributes:
        llm_client: LLM client for generating workouts
        config: Application configuration
        prompt_template: System prompt for workout generation
    """

    def __init__(self, llm_client: LLMClient, config: AppConfig):
        """Initialize workout service.

        Args:
            llm_client: Initialized LLM client
            config: Application configuration
        """
        self.llm_client = llm_client
        self.config = config
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load workout generator system prompt.

        Returns:
            Prompt template content
        """
        prompt_path = self.config.prompts_dir / "workout_generator_prompt.txt"
        with open(prompt_path, 'r') as f:
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
            {"role": "system", "content": self.prompt_template},
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
