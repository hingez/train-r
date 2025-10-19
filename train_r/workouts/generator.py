"""Generate ZWO workout files using Gemini."""
import re
import time
import logging
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai.types import GenerateContentConfig
from google.api_core import exceptions as google_exceptions

from train_r.core.config import GEMINI_MODEL_NAME, GEMINI_TEMPERATURE

# Get project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
RETRY_BACKOFF_MULTIPLIER = 2


def load_workout_prompt() -> str:
    """Load the workout generator system prompt."""
    prompt_path = PROJECT_ROOT / "prompts" / "workout_generator_prompt.txt"
    with open(prompt_path, 'r') as f:
        return f.read()


def generate_workout(
    client_ftp: int,
    workout_duration: int,
    workout_type: str,
    api_key: str
) -> str:
    """Generate a ZWO workout file using Gemini.

    Args:
        client_ftp: Client's FTP in watts
        workout_duration: Duration in seconds
        workout_type: Type of workout (e.g., "Sweet Spot", "Threshold")
        api_key: Gemini API key

    Returns:
        ZWO file content as string

    Raises:
        Exception: If workout generation fails
    """
    # Load system prompt
    system_prompt = load_workout_prompt()

    # Build user prompt with parameters
    user_prompt = f"""Generate a workout with the following parameters:

FTP: {client_ftp}W
Duration: {workout_duration} seconds ({workout_duration // 60} minutes)
Type: {workout_type}

Return ONLY the ZWO XML file content, nothing else."""

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    logger = logging.getLogger('train-r')

    # Generate workout with retry logic
    last_exception = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=user_prompt,
                config=GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=GEMINI_TEMPERATURE
                )
            )

            # Extract text
            zwo_content = response.text.strip()

            # Basic validation - ensure it has workout_file tags
            if "<workout_file>" not in zwo_content or "</workout_file>" not in zwo_content:
                raise ValueError("Generated workout is missing required XML structure")

            # If we had retries, log success
            if attempt > 0:
                logger.info(f"Workout generation successful on attempt {attempt + 1}")

            return zwo_content

        except (google_exceptions.GoogleAPIError, ValueError) as e:
            last_exception = e

            # Don't retry on validation errors (ValueError)
            if isinstance(e, ValueError):
                logger.error(f"Workout validation failed: {str(e)}")
                raise

            # Retry on API errors
            if attempt < MAX_RETRIES - 1:
                delay = INITIAL_RETRY_DELAY * (RETRY_BACKOFF_MULTIPLIER ** attempt)
                logger.warning(
                    f"Workout generation attempt {attempt + 1} failed: {str(e)}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
            else:
                logger.error(f"Workout generation failed after {MAX_RETRIES} attempts")

    # If we get here, all retries failed
    raise last_exception


def save_workout(zwo_content: str, workout_type: str) -> str:
    """Save ZWO workout to file.

    Args:
        zwo_content: ZWO file content
        workout_type: Type of workout for filename

    Returns:
        Path to saved file
    """
    # Create directory if needed
    output_dir = PROJECT_ROOT / "data" / "created_workouts"
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

    return str(filepath)
