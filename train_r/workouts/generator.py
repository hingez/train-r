"""Generate ZWO workout files using Gemini."""
import re
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai.types import GenerateContentConfig


def load_workout_prompt() -> str:
    """Load the workout generator system prompt."""
    with open("prompts/workout_generator_prompt.txt", 'r') as f:
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

    # Generate workout
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0
        )
    )

    # Extract text
    zwo_content = response.text.strip()

    # Basic validation - ensure it has workout_file tags
    if "<workout_file>" not in zwo_content or "</workout_file>" not in zwo_content:
        raise ValueError("Generated workout is missing required XML structure")

    return zwo_content


def save_workout(zwo_content: str, workout_type: str) -> str:
    """Save ZWO workout to file.

    Args:
        zwo_content: ZWO file content
        workout_type: Type of workout for filename

    Returns:
        Path to saved file
    """
    # Create directory if needed
    output_dir = Path("data/created_workouts")
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
