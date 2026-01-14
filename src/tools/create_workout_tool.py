"""Create workout tool implementation."""
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

from src.config import AppConfig
from src.utils.zwo_parser import parse_zwo_content

# Import for type hints only to avoid circular dependency
if TYPE_CHECKING:
    from src.services.coach_service import CoachService


def _validate_workout_params(
    client_ftp: Optional[int],
    workout_duration: Optional[int],
    workout_description: Optional[str],
    config: AppConfig
) -> Tuple[bool, Optional[str]]:
    """Validate workout parameters before processing.

    Args:
        client_ftp: Client's FTP in watts
        workout_duration: Duration in seconds
        workout_description: Description of workout structure and goals
        config: Application configuration with validation limits

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for missing parameters
    if client_ftp is None:
        return False, "client_ftp is required"
    if workout_duration is None:
        return False, "workout_duration is required"
    if workout_description is None:
        return False, "workout_description is required"

    # Validate FTP
    if not isinstance(client_ftp, int):
        return False, f"client_ftp must be an integer, got {type(client_ftp).__name__}"
    if client_ftp < config.workout_min_ftp:
        return False, f"client_ftp must be at least {config.workout_min_ftp}W, got {client_ftp}W"
    if client_ftp > config.workout_max_ftp:
        return False, f"client_ftp must be at most {config.workout_max_ftp}W, got {client_ftp}W"

    # Validate duration
    if not isinstance(workout_duration, int):
        return False, f"workout_duration must be an integer, got {type(workout_duration).__name__}"
    if workout_duration < config.workout_min_duration:
        return False, f"workout_duration must be at least {config.workout_min_duration}s (1 minute), got {workout_duration}s"
    if workout_duration > config.workout_max_duration:
        return False, f"workout_duration must be at most {config.workout_max_duration}s (4 hours), got {workout_duration}s"

    # Validate workout description
    if not isinstance(workout_description, str):
        return False, f"workout_description must be a string, got {type(workout_description).__name__}"
    if not workout_description.strip():
        return False, "workout_description cannot be empty"

    return True, None


def execute(
    args: dict,
    config: AppConfig,
    coach_service: "CoachService"
) -> dict:
    """Execute create_one_off_workout tool.

    Args:
        args: Tool arguments (client_ftp, workout_duration, workout_description)
        config: Application configuration with API keys
        coach_service: CoachService instance for workout generation

    Returns:
        Result dict with workout details
    """
    logger = logging.getLogger('train-r')

    # Log tool start and begin timing
    logger.info(f"TOOL_START tool=create_one_off_workout args={args}")
    start_time = time.time()

    try:
        # Extract parameters
        client_ftp = args.get("client_ftp")
        workout_duration = args.get("workout_duration")
        workout_description = args.get("workout_description")

        # Validate parameters
        is_valid, error_msg = _validate_workout_params(client_ftp, workout_duration, workout_description, config)
        if not is_valid:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TOOL_ERROR tool=create_one_off_workout duration={duration_ms}ms error=Parameter validation failed: {error_msg}")
            return {
                "success": False,
                "error": f"Invalid parameters: {error_msg}",
                "message": f"Validation error: {error_msg}"
            }

        logger.info(f"Generating workout: FTP={client_ftp}W, Duration={workout_duration}s, Description={workout_description[:50]}...")

        # Build complete workout description with structured parameters
        full_description = f"""FTP: {client_ftp}W
Duration: {workout_duration} seconds ({workout_duration // 60} minutes)
Workout: {workout_description}"""

        # Generate workout using workout generator (but don't save yet)
        # Pass session_id for LangSmith thread grouping
        zwo_content = coach_service.workout_generator.generate_workout(
            workout_description=full_description,
            session_id=coach_service.current_session_id
        )

        logger.info("Workout generated successfully")

        # Parse ZWO content for visualization
        try:
            workout_data = parse_zwo_content(zwo_content, client_ftp)
            logger.info(f"Parsed workout into {len(workout_data['segments'])} segments")
        except Exception as e:
            logger.error(f"Failed to parse ZWO content: {e}", exc_info=True)
            # Continue without workout data - visualization will use mock data
            workout_data = None

        # Calculate schedule time using configured hours
        schedule_time = datetime.now() + timedelta(hours=config.workout_schedule_hours)
        schedule_time_str = schedule_time.strftime("%Y-%m-%dT%H:%M:%S")

        logger.info(f"Workout created for scheduling at: {schedule_time_str}")

        # Generate external ID and filename for later use
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        external_id = f"train-r-{timestamp}"
        # Extract workout name from description (first 30 chars, sanitized)
        workout_name = workout_description[:30].strip()

        # Return success result with workout content (will be saved/uploaded after user confirmation)
        result = {
            "success": True,
            "zwo_content": zwo_content,
            "filename": f"{timestamp}.zwo",  # Will be renamed when saved
            "workout_name": workout_name,
            "workout_description": workout_description,
            "scheduled_time": schedule_time_str,
            "external_id": external_id,
            "message": f"Workout created and ready to schedule for {schedule_time_str}"
        }

        # Add parsed workout data if available
        if workout_data:
            result["workout_data"] = workout_data

        # Log successful completion with timing
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(f"TOOL_END tool=create_one_off_workout duration={duration_ms}ms success=True")

        return result

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"TOOL_ERROR tool=create_one_off_workout duration={duration_ms}ms error={str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create workout: {str(e)}"
        }
