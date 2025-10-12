"""Tool execution handler with logging."""
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Any
from pathlib import Path

from train_r.workouts.generator import generate_workout, save_workout
from train_r.integrations.intervals import IntervalsUploader


def handle_tool_call(tool_call: Any, gemini_api_key: str, intervals_api_key: str) -> dict:
    """Handle a tool call from the model.

    Args:
        tool_call: Tool call object from Gemini response
        gemini_api_key: API key for Gemini
        intervals_api_key: API key for intervals.icu

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
        result = _handle_create_workout(tool_args, gemini_api_key, intervals_api_key)
    else:
        # Other tools return dummy response for now
        result = {"result": "tool run successfully"}

    logger.info(f"TOOL_RESULT: {json.dumps(result, indent=2)}")
    logger.info("-" * 60)

    return result


def _handle_create_workout(args: dict, gemini_api_key: str, intervals_api_key: str) -> dict:
    """Handle create_one_off_workout tool call.

    Args:
        args: Tool arguments (client_ftp, workout_duration, workout_type)
        gemini_api_key: API key for Gemini
        intervals_api_key: API key for intervals.icu

    Returns:
        Result dict with workout details
    """
    logger = logging.getLogger('train-r')

    try:
        # Extract parameters
        client_ftp = args.get("client_ftp")
        workout_duration = args.get("workout_duration")
        workout_type = args.get("workout_type")

        logger.info(f"Generating workout: FTP={client_ftp}W, Duration={workout_duration}s, Type={workout_type}")

        # Generate workout using Gemini
        zwo_content = generate_workout(
            client_ftp=client_ftp,
            workout_duration=workout_duration,
            workout_type=workout_type,
            api_key=gemini_api_key
        )

        logger.info("Workout generated successfully")

        # Save workout to file
        filepath = save_workout(zwo_content, workout_type)
        logger.info(f"Workout saved to: {filepath}")

        # Calculate schedule time (1 hour from now)
        schedule_time = datetime.now() + timedelta(hours=1)
        schedule_time_str = schedule_time.strftime("%Y-%m-%dT%H:%M:%S")

        logger.info(f"Scheduling workout for: {schedule_time_str}")

        # Initialize uploader
        uploader = IntervalsUploader(api_key=intervals_api_key)

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
