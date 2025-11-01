"""Centralized configuration management for Train-R.

This module consolidates all configuration including:
- Environment variables
- Model configuration
- Application settings
- Path configuration
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get project root (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent

# Model configuration constants
GEMINI_MODEL_NAME = "gemini-2.5-flash"
GEMINI_TEMPERATURE = 0
DEFAULT_WORKOUT_SCHEDULE_HOURS = 1
DEFAULT_ATHLETE_ID = "0"


@dataclass
class AppConfig:
    """Application configuration container.

    This class consolidates all application configuration from environment
    variables and provides default values following the Single Responsibility
    Principle - one source of truth for all config.

    Attributes:
        gemini_api_key: API key for Google Gemini (from environment)
        intervals_api_key: API key for intervals.icu (from environment)
        project_root: Root directory of the project
        prompts_dir: Directory containing prompt templates
        data_dir: Directory for data storage
        logs_dir: Directory for application logs
        tools_dir: Directory containing tool definitions
        workouts_dir: Directory for saved workout files
        model_name: LLM model identifier (default: gemini-2.5-flash)
        temperature: Model temperature setting (default: 0)
        workout_schedule_hours: Hours in the future to schedule workouts (default: 1)
        default_athlete_id: Default athlete ID for intervals.icu (default: "0" = authenticated user)
        cors_origins: List of allowed CORS origins for API (default: ["http://localhost:5173"])
    """
    # API Keys
    gemini_api_key: str
    intervals_api_key: str

    # Paths
    project_root: Path
    prompts_dir: Path
    data_dir: Path
    logs_dir: Path
    tools_dir: Path
    workouts_dir: Path
    history_dir: Path

    # LLM Settings
    model_name: str = GEMINI_MODEL_NAME
    temperature: float = GEMINI_TEMPERATURE

    # Application Settings
    workout_schedule_hours: int = DEFAULT_WORKOUT_SCHEDULE_HOURS
    default_athlete_id: str = DEFAULT_ATHLETE_ID
    cors_origins: list[str] = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables.

        Reads from .env file if present, otherwise uses system environment.

        Returns:
            AppConfig instance with all settings

        Raises:
            ValueError: If required environment variables are missing
        """
        # Get required API keys
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        intervals_api_key = os.getenv("INTERVALS_API_KEY")

        if not gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment. "
                "Please set it in .env file or environment variables."
            )

        if not intervals_api_key:
            raise ValueError(
                "INTERVALS_API_KEY not found in environment. "
                "Please set it in .env file or environment variables."
            )

        # Get athlete ID (try both old typo and corrected spelling for backward compatibility)
        athlete_id = os.getenv("INTERVALS_ATHLETE_ID") or os.getenv("INTERVALS_ATHELETE_ID") or DEFAULT_ATHLETE_ID

        # Build paths
        prompts_dir = PROJECT_ROOT / "prompts"
        data_dir = PROJECT_ROOT / "data"
        logs_dir = PROJECT_ROOT / "logs"
        tools_dir = PROJECT_ROOT / "src" / "tools" / "definitions"
        workouts_dir = data_dir / "created_workouts"
        history_dir = data_dir / "workout_history"

        # Get CORS origins (default to localhost:5173 for frontend)
        cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

        return cls(
            gemini_api_key=gemini_api_key,
            intervals_api_key=intervals_api_key,
            project_root=PROJECT_ROOT,
            prompts_dir=prompts_dir,
            data_dir=data_dir,
            logs_dir=logs_dir,
            tools_dir=tools_dir,
            workouts_dir=workouts_dir,
            history_dir=history_dir,
            cors_origins=cors_origins,
            default_athlete_id=athlete_id,
        )

    def create_directories(self):
        """Create required directories if they don't exist.

        This is separated from config loading to avoid side effects
        during configuration initialization.
        """
        self.logs_dir.mkdir(exist_ok=True)
        self.workouts_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def validate(self) -> bool:
        """Validate that all required paths and settings exist.

        Returns:
            True if configuration is valid

        Raises:
            FileNotFoundError: If required directories are missing
        """
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")

        if not self.tools_dir.exists():
            raise FileNotFoundError(f"Tools directory not found: {self.tools_dir}")

        return True
