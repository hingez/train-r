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

# ============================================================
# MODULE-LEVEL CONSTANTS (Defaults)
# ============================================================
#
# These constants define the default behavior of Train-R. You can override
# many of these by setting environment variables in your .env file.
# See .env.example for available overrides.
#
# Organization:
# - LLM Configuration: AI model settings
# - Network & API: Server ports and API endpoints
# - Retry Configuration: How API failures are handled
# - Workout Validation: Limits for generated workouts
# - History & Analysis: Default time periods for analysis
# - Application Defaults: General app behavior
# - Logging: Debug and error tracking
# - Application Metadata: Version info
#

# ─────────────────────────────────────────────────────────────
# LLM Configuration
# ─────────────────────────────────────────────────────────────
LLM_MODEL_NAME = "gemini-2.5-flash"  # AI model to use for coaching
LLM_TEMPERATURE = 0  # 0 = deterministic, higher = more creative
LLM_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"  # Gemini's OpenAI-compatible endpoint

# ─────────────────────────────────────────────────────────────
# Network & API Configuration
# ─────────────────────────────────────────────────────────────
INTERVALS_BASE_URL = "https://intervals.icu/api/v1"  # intervals.icu API endpoint
INTERVALS_API_TIMEOUT = 30  # Maximum seconds to wait for intervals.icu responses
BACKEND_HOST = "0.0.0.0"  # Server host (0.0.0.0 = all interfaces)
BACKEND_PORT = 3000  # Port for backend API server
FRONTEND_PORT = 3001  # Port for frontend dev server

# ─────────────────────────────────────────────────────────────
# Retry Configuration
# ─────────────────────────────────────────────────────────────
# When API calls fail, Train-R retries with exponential backoff
API_MAX_RETRIES = 3  # Maximum retry attempts before giving up
API_INITIAL_RETRY_DELAY = 1  # Seconds to wait before first retry
API_RETRY_BACKOFF_MULTIPLIER = 2  # Each retry waits 2x longer (1s, 2s, 4s, etc.)

# ─────────────────────────────────────────────────────────────
# Workout Validation Limits
# ─────────────────────────────────────────────────────────────
# These limits ensure generated workouts are reasonable
WORKOUT_MIN_FTP = 50  # Minimum FTP in watts (beginner level)
WORKOUT_MAX_FTP = 600  # Maximum FTP in watts (elite level)
WORKOUT_MIN_DURATION = 60  # Minimum workout duration: 1 minute
WORKOUT_MAX_DURATION = 14400  # Maximum workout duration: 4 hours

# ─────────────────────────────────────────────────────────────
# History & Analysis Defaults
# ─────────────────────────────────────────────────────────────
HISTORY_DEFAULT_LOOKBACK_DAYS = 365  # Default history window: 12 months
POWER_CURVE_TIME_PERIODS_MONTHS = [1, 2, 3, 6, 12]  # Analysis periods: 1mo, 2mo, 3mo, 6mo, 12mo
# Power curve durations: 15s, 30s, 1m, 2m, 3m, 5m, 10m, 15m, 20m, 30m, 45m, 60m
POWER_CURVE_DURATIONS_SECONDS = [15, 30, 60, 120, 180, 300, 600, 900, 1200, 1800, 2700, 3600]

# ─────────────────────────────────────────────────────────────
# Application Defaults
# ─────────────────────────────────────────────────────────────
DEFAULT_WORKOUT_SCHEDULE_HOURS = 1  # Schedule workouts 1 hour in the future by default
DEFAULT_ATHLETE_ID = "0"  # "0" means use the authenticated user's athlete ID
DEFAULT_MAX_TOOL_ITERATIONS = 10  # Safety limit for AI tool-calling loops
UPLOAD_DEFAULT_HOUR = 9  # Default upload time: 9:00 AM
UPLOAD_DEFAULT_MINUTE = 0  # Default upload minute

# ─────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────
LOG_FILENAME = "train-r.log"  # Name of log file in logs/ directory
LOG_LEVEL = "INFO"  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL

# ─────────────────────────────────────────────────────────────
# Application Metadata
# ─────────────────────────────────────────────────────────────
APP_VERSION = "0.2.0"  # Current version of Train-R


@dataclass
class AppConfig:
    """Application configuration container.

    This class consolidates all application configuration from environment
    variables and provides default values following the Single Responsibility
    Principle - one source of truth for all config.

    Attributes:
        llm_api_key: API key for LLM provider (from environment)
        intervals_api_key: API key for intervals.icu (from environment)
        project_root: Root directory of the project
        prompts_dir: Directory containing prompt templates
        data_dir: Directory for data storage
        logs_dir: Directory for application logs
        tools_dir: Directory containing tool definitions
        workouts_dir: Directory for saved workout files
        history_dir: Directory for workout history data
        model_name: LLM model identifier
        temperature: Model temperature setting
        llm_base_url: Base URL for LLM API
        reasoning_effort: Optional reasoning effort level
        intervals_base_url: Base URL for intervals.icu API
        intervals_api_timeout: Timeout for intervals.icu requests (seconds)
        backend_host: Host for backend server
        backend_port: Port for backend server
        frontend_port: Port for frontend dev server
        api_max_retries: Maximum API retry attempts
        api_initial_retry_delay: Initial retry delay (seconds)
        api_retry_backoff_multiplier: Backoff multiplier for retries
        workout_min_ftp: Minimum valid FTP (watts)
        workout_max_ftp: Maximum valid FTP (watts)
        workout_min_duration: Minimum workout duration (seconds)
        workout_max_duration: Maximum workout duration (seconds)
        history_default_lookback_days: Default history lookback period
        power_curve_time_periods_months: Time periods for power curve analysis
        power_curve_durations_seconds: Duration points for power curve
        workout_schedule_hours: Hours in the future to schedule workouts
        default_athlete_id: Default athlete ID for intervals.icu
        max_tool_iterations: Maximum iterations for tool calling loop
        upload_default_hour: Default hour for workout uploads
        upload_default_minute: Default minute for workout uploads
        log_filename: Log file name
        log_level: Logging level
        app_version: Application version
        cors_origins: List of allowed CORS origins for API
    """
    # API Keys
    llm_api_key: str
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
    model_name: str = LLM_MODEL_NAME
    temperature: float = LLM_TEMPERATURE
    llm_base_url: str = LLM_BASE_URL
    reasoning_effort: Optional[str] = None

    # Network & API Configuration
    intervals_base_url: str = INTERVALS_BASE_URL
    intervals_api_timeout: int = INTERVALS_API_TIMEOUT
    backend_host: str = BACKEND_HOST
    backend_port: int = BACKEND_PORT
    frontend_port: int = FRONTEND_PORT

    # Retry Configuration
    api_max_retries: int = API_MAX_RETRIES
    api_initial_retry_delay: int = API_INITIAL_RETRY_DELAY
    api_retry_backoff_multiplier: int = API_RETRY_BACKOFF_MULTIPLIER

    # Workout Validation Limits
    workout_min_ftp: int = WORKOUT_MIN_FTP
    workout_max_ftp: int = WORKOUT_MAX_FTP
    workout_min_duration: int = WORKOUT_MIN_DURATION
    workout_max_duration: int = WORKOUT_MAX_DURATION

    # History & Analysis Defaults
    history_default_lookback_days: int = HISTORY_DEFAULT_LOOKBACK_DAYS
    power_curve_time_periods_months: list[int] = None
    power_curve_durations_seconds: list[int] = None

    # Application Settings
    workout_schedule_hours: int = DEFAULT_WORKOUT_SCHEDULE_HOURS
    default_athlete_id: str = DEFAULT_ATHLETE_ID
    max_tool_iterations: int = DEFAULT_MAX_TOOL_ITERATIONS
    upload_default_hour: int = UPLOAD_DEFAULT_HOUR
    upload_default_minute: int = UPLOAD_DEFAULT_MINUTE

    # Logging Configuration
    log_filename: str = LOG_FILENAME
    log_level: str = LOG_LEVEL

    # Application Metadata
    app_version: str = APP_VERSION

    # CORS Configuration
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
        # Get required API keys (support both new and legacy env var names)
        llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
        intervals_api_key = os.getenv("INTERVALS_API_KEY")

        if not llm_api_key:
            raise ValueError(
                "LLM_API_KEY not found in environment. "
                "Please set it in .env file or environment variables. "
                "(Legacy GEMINI_API_KEY is also supported)"
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

        # Get CORS origins (default to localhost:3001 for frontend)
        cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3001")
        cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

        # Get reasoning effort if specified
        reasoning_effort = os.getenv("REASONING_EFFORT")  # Can be "low", "medium", "high", "none", or None

        # Get optional overrides from environment
        backend_host = os.getenv("BACKEND_HOST", BACKEND_HOST)
        backend_port = int(os.getenv("BACKEND_PORT", BACKEND_PORT))
        frontend_port = int(os.getenv("FRONTEND_PORT", FRONTEND_PORT))
        llm_base_url = os.getenv("LLM_BASE_URL", LLM_BASE_URL)
        intervals_base_url = os.getenv("INTERVALS_BASE_URL", INTERVALS_BASE_URL)
        intervals_api_timeout = int(os.getenv("INTERVALS_API_TIMEOUT", INTERVALS_API_TIMEOUT))
        log_level = os.getenv("LOG_LEVEL", LOG_LEVEL)

        return cls(
            llm_api_key=llm_api_key,
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
            reasoning_effort=reasoning_effort,
            backend_host=backend_host,
            backend_port=backend_port,
            frontend_port=frontend_port,
            llm_base_url=llm_base_url,
            intervals_base_url=intervals_base_url,
            intervals_api_timeout=intervals_api_timeout,
            log_level=log_level,
            power_curve_time_periods_months=POWER_CURVE_TIME_PERIODS_MONTHS.copy(),
            power_curve_durations_seconds=POWER_CURVE_DURATIONS_SECONDS.copy(),
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
