"""Tool execution handler with logging."""
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING
from pathlib import Path

from src.config import AppConfig

# Updated imports to use new src/ structure
from src.integrations.intervals import IntervalsClient

# Import for type hints only to avoid circular dependency
if TYPE_CHECKING:
    from src.services.coach_service import CoachService

# Validation constants
MIN_FTP = 50  # Minimum reasonable FTP in watts
MAX_FTP = 600  # Maximum reasonable FTP in watts
MIN_DURATION = 60  # Minimum duration: 1 minute
MAX_DURATION = 14400  # Maximum duration: 4 hours


def handle_tool_call(
    tool_call: Any,
    config: AppConfig,
    coach_service: "CoachService"
) -> dict:
    """Handle a tool call from the model.

    Args:
        tool_call: Tool call object with name and args attributes
        config: Application configuration with API keys
        coach_service: CoachService instance for workout generation

    Returns:
        Result dict from tool execution
    """
    logger = logging.getLogger('train-r')

    # Extract tool call details
    tool_name = tool_call.name
    tool_args = tool_call.args

    # Log the tool call
    logger.info(f"TOOL_CALL: {tool_name}")
    logger.info(f"TOOL_ARGS: {json.dumps(tool_args, indent=2)}")

    # Route to appropriate handler using dictionary dispatch
    handler = _get_tool_handler(tool_name)
    if handler:
        result = handler(tool_args, config, coach_service)
    else:
        # Unknown tools return dummy response
        logger.warning(f"No handler found for tool: {tool_name}")
        result = {"result": "tool run successfully"}

    logger.info(f"TOOL_RESULT: {json.dumps(result, indent=2)}")
    logger.info("-" * 60)

    return result


def _get_tool_handler(tool_name: str):
    """Get the handler function for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Handler function or None if not found
    """
    # Tool handler registry - maps tool names to handler functions
    handlers = {
        "create_one_off_workout": _handle_create_workout,
        "get_history": _handle_get_history,
    }
    return handlers.get(tool_name)


def _validate_workout_params(
    client_ftp: Optional[int],
    workout_duration: Optional[int],
    workout_type: Optional[str]
) -> Tuple[bool, Optional[str]]:
    """Validate workout parameters before processing.

    Args:
        client_ftp: Client's FTP in watts
        workout_duration: Duration in seconds
        workout_type: Type of workout

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
    if client_ftp < MIN_FTP:
        return False, f"client_ftp must be at least {MIN_FTP}W, got {client_ftp}W"
    if client_ftp > MAX_FTP:
        return False, f"client_ftp must be at most {MAX_FTP}W, got {client_ftp}W"

    # Validate duration
    if not isinstance(workout_duration, int):
        return False, f"workout_duration must be an integer, got {type(workout_duration).__name__}"
    if workout_duration < MIN_DURATION:
        return False, f"workout_duration must be at least {MIN_DURATION}s (1 minute), got {workout_duration}s"
    if workout_duration > MAX_DURATION:
        return False, f"workout_duration must be at most {MAX_DURATION}s (4 hours), got {workout_duration}s"

    # Validate workout type
    if not isinstance(workout_type, str):
        return False, f"workout_type must be a string, got {type(workout_type).__name__}"
    if not workout_type.strip():
        return False, "workout_type cannot be empty"

    return True, None


def _handle_create_workout(
    args: dict,
    config: AppConfig,
    coach_service: "CoachService"
) -> dict:
    """Handle create_one_off_workout tool call.

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
        is_valid, error_msg = _validate_workout_params(client_ftp, workout_duration, workout_type)
        if not is_valid:
            logger.error(f"Parameter validation failed: {error_msg}")
            return {
                "success": False,
                "error": f"Invalid parameters: {error_msg}",
                "message": f"Validation error: {error_msg}"
            }

        logger.info(f"Generating workout: FTP={client_ftp}W, Duration={workout_duration}s, Type={workout_type}")

        # Generate workout using coach service
        zwo_content = coach_service.generate_workout(
            client_ftp=client_ftp,
            workout_duration=workout_duration,
            workout_type=workout_type
        )

        logger.info("Workout generated successfully")

        # Save workout to file
        filepath = coach_service.save_workout(zwo_content, workout_type)
        logger.info(f"Workout saved to: {filepath}")

        # Calculate schedule time using configured hours
        schedule_time = datetime.now() + timedelta(hours=config.workout_schedule_hours)
        schedule_time_str = schedule_time.strftime("%Y-%m-%dT%H:%M:%S")

        logger.info(f"Scheduling workout for: {schedule_time_str}")

        # Initialize intervals.icu client
        intervals_client = IntervalsClient(api_key=config.intervals_api_key)

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


def _handle_get_history(
    args: dict,
    config: AppConfig
) -> dict:
    """Handle get_history tool call.

    Args:
        args: Tool arguments (oldest_date, newest_date - both optional)
        config: Application configuration with API keys and paths

    Returns:
        Result dict with confirmation message
    """
    logger = logging.getLogger('train-r')

    try:
        # Extract optional parameters
        oldest_date = args.get("oldest_date")
        newest_date = args.get("newest_date")

        logger.info(f"Fetching workout history (oldest={oldest_date}, newest={newest_date})")

        # Initialize intervals.icu client
        intervals_client = IntervalsClient(api_key=config.intervals_api_key)

        # Fetch workout history
        history = intervals_client.get_workout_history(
            oldest_date=oldest_date,
            newest_date=newest_date
        )

        logger.info(f"Retrieved {len(history)} workouts from intervals.icu")

        # Ensure history directory exists
        history_dir = config.data_dir / "workout_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        # Save history to JSON file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"history_{timestamp}.json"
        filepath = history_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        logger.info(f"Workout history saved to: {filepath}")

        # Return simple confirmation (data manipulation comes later)
        return {
            "success": True,
            "message": "history fetched",
            "workout_count": len(history),
            "saved_to": str(filepath)
        }

    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch history: {str(e)}"
        }
