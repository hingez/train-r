"""Tool execution handler with logging."""
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from pathlib import Path

from train_r.core.config import AppConfig
from train_r.workouts.generator import generate_workout, save_workout
from train_r.integrations.intervals import IntervalsUploader

# Validation constants
MIN_FTP = 50  # Minimum reasonable FTP in watts
MAX_FTP = 600  # Maximum reasonable FTP in watts
MIN_DURATION = 60  # Minimum duration: 1 minute
MAX_DURATION = 14400  # Maximum duration: 4 hours


def handle_tool_call(tool_call: Any, config: AppConfig) -> dict:
    """Handle a tool call from the model.

    Args:
        tool_call: Tool call object from Gemini response
        config: Application configuration with API keys

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

    # Route to appropriate handler
    if tool_name == "create_one_off_workout":
        result = _handle_create_workout(tool_args, config)
    else:
        # Other tools return dummy response for now
        result = {"result": "tool run successfully"}

    logger.info(f"TOOL_RESULT: {json.dumps(result, indent=2)}")
    logger.info("-" * 60)

    return result


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


def _handle_create_workout(args: dict, config: AppConfig) -> dict:
    """Handle create_one_off_workout tool call.

    Args:
        args: Tool arguments (client_ftp, workout_duration, workout_type)
        config: Application configuration with API keys

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

        # Generate workout using Gemini
        zwo_content = generate_workout(
            client_ftp=client_ftp,
            workout_duration=workout_duration,
            workout_type=workout_type,
            api_key=config.gemini_api_key
        )

        logger.info("Workout generated successfully")

        # Save workout to file
        filepath = save_workout(zwo_content, workout_type)
        logger.info(f"Workout saved to: {filepath}")

        # Calculate schedule time using configured hours
        schedule_time = datetime.now() + timedelta(hours=config.workout_schedule_hours)
        schedule_time_str = schedule_time.strftime("%Y-%m-%dT%H:%M:%S")

        logger.info(f"Scheduling workout for: {schedule_time_str}")

        # Initialize uploader
        uploader = IntervalsUploader(api_key=config.intervals_api_key)

        # Generate external ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        external_id = f"train-r-{timestamp}"

        # Upload workout
        response = uploader.upload_workout(
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
