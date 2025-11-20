"""Create workout tool implementation."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

from src.config import AppConfig
from src.integrations.intervals import IntervalsClient

# Import for type hints only to avoid circular dependency
if TYPE_CHECKING:
    from src.services.coach_service import CoachService


def _validate_workout_params(
    client_ftp: Optional[int],
    workout_duration: Optional[int],
    workout_type: Optional[str],
    config: AppConfig
) -> Tuple[bool, Optional[str]]:
    """Validate workout parameters before processing.

    Args:
        client_ftp: Client's FTP in watts
        workout_duration: Duration in seconds
        workout_type: Type of workout
        config: Application configuration with validation limits

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for missing parameters
    if client_ftp is None:
        return False, "client_ftp is required"
    if workout_duration is None:
        return False, "workout_duration is required"
    if workout_type is None:
        return False, "workout_type is required"

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

    # Validate workout type
    if not isinstance(workout_type, str):
        return False, f"workout_type must be a string, got {type(workout_type).__name__}"
    if not workout_type.strip():
        return False, "workout_type cannot be empty"

    return True, None


def execute(
    args: dict,
    config: AppConfig,
    coach_service: "CoachService"
) -> dict:
    """Execute create_one_off_workout tool.

    Args:
        args: Tool arguments (client_ftp, workout_duration, workout_type)
        config: Application configuration with API keys
        coach_service: CoachService instance for workout generation

    Returns:
        Result dict with workout details
    """
    logger = logging.getLogger('train-r')

    try:
        # Extract parameters
        client_ftp = args.get("client_ftp")
        workout_duration = args.get("workout_duration")
        workout_type = args.get("workout_type")

        # Validate parameters
        is_valid, error_msg = _validate_workout_params(client_ftp, workout_duration, workout_type, config)
        if not is_valid:
            logger.error(f"Parameter validation failed: {error_msg}")
            return {
                "success": False,
                "error": f"Invalid parameters: {error_msg}",
                "message": f"Validation error: {error_msg}"
            }

        logger.info(f"Generating workout: FTP={client_ftp}W, Duration={workout_duration}s, Type={workout_type}")

        # Generate workout using workout generator
        zwo_content = coach_service.workout_generator.generate_workout(
            client_ftp=client_ftp,
            workout_duration=workout_duration,
            workout_type=workout_type
        )

        logger.info("Workout generated successfully")

        # Save workout to file
        filepath = coach_service.workout_generator.save_workout(zwo_content, workout_type)
        logger.info(f"Workout saved to: {filepath}")

        # Calculate schedule time using configured hours
        schedule_time = datetime.now() + timedelta(hours=config.workout_schedule_hours)
        schedule_time_str = schedule_time.strftime("%Y-%m-%dT%H:%M:%S")

        logger.info(f"Scheduling workout for: {schedule_time_str}")

        # Initialize intervals.icu client
        intervals_client = IntervalsClient(api_key=config.intervals_api_key, config=config)

        # Generate external ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        external_id = f"train-r-{timestamp}"

        # Upload workout
        response = intervals_client.upload_workout(
            file_path=filepath,
            start_date=schedule_time_str,
            external_id=external_id
        )

        logger.info(f"Upload successful - Event ID: {response.get('id')}")

        # Return success result
        return {
            "success": True,
            "workout_file": filepath,
            "event_id": response.get("id"),
            "event_name": response.get("name"),
            "scheduled_time": schedule_time_str,
            "message": f"Workout created and scheduled for {schedule_time_str}"
        }

    except Exception as e:
        logger.error(f"Error creating workout: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create workout: {str(e)}"
        }
