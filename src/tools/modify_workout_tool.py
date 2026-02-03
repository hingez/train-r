"""Tool for modifying planned workouts in the training plan."""
import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Tuple

from src.config import AppConfig
from src.services.current_plan_service import CurrentPlanService
from src.utils.zwo_parser import parse_zwo_content

if TYPE_CHECKING:
    from src.services.coach_service import CoachService

logger = logging.getLogger("train-r")


def execute(args: dict, config: AppConfig, coach_service: "CoachService" = None) -> dict:
    """
    Modify planned workout: validate → generate ZWO → delete old → create new → update current plan

    Args:
        args: {"event_id": int, "workout_description": str}
        config: AppConfig instance
        coach_service: CoachService instance

    Returns:
        {
            "success": True,
            "date": "2026-01-15",
            "original_type": "Sweet Spot",
            "new_type": "Recovery",
            "deleted_event_id": 88597871,
            "new_event_id": 88598012,
            "message": "Workout modified successfully"
        }
    """
    # Log tool start and begin timing
    logger.info(f"TOOL_START tool=modify_workout args={args}")
    start_time = time.time()

    try:
        # Extract parameters
        event_id = args.get("event_id")
        workout_description = args.get("workout_description", "")

        # Validate parameters
        if not event_id or not isinstance(event_id, int):
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TOOL_ERROR tool=modify_workout duration={duration_ms}ms error=event_id validation failed")
            return {
                "success": False,
                "message": "event_id is required and must be an integer"
            }

        if not workout_description:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TOOL_ERROR tool=modify_workout duration={duration_ms}ms error=workout_description is required")
            return {
                "success": False,
                "message": "workout_description is required"
            }

        # Initialize CurrentPlanService
        current_plan_service = CurrentPlanService(config)

        # Create IntervalsClient
        from src.integrations.intervals import IntervalsClient
        try:
            intervals_client = IntervalsClient(
                api_key=config.intervals_api_key,
                config=config
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TOOL_ERROR tool=modify_workout duration={duration_ms}ms error=Failed to create intervals client: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to connect to intervals.icu: {str(e)}"
            }

        # Validate modification parameters
        is_valid, error_message, workout_result = _validate_modify_params(
            event_id,
            current_plan_service,
            intervals_client
        )

        if not is_valid:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TOOL_ERROR tool=modify_workout duration={duration_ms}ms error={error_message}")
            return {
                "success": False,
                "message": error_message,
                "error": error_message
            }

        date_str, workout = workout_result
        athlete_ftp = current_plan_service.load_current_plan().get("athlete_ftp", 365)

        logger.info(f"Modifying workout for date {date_str} (event_id: {event_id})")

        # Build LLM prompt with context
        prompt = _build_llm_prompt(workout, workout_description, athlete_ftp)

        # Generate new ZWO via WorkoutGenerator
        logger.info("Generating new ZWO file via LLM")
        zwo_content = coach_service.workout_generator.generate_workout(
            workout_description=prompt
        )

        # Parse ZWO to extract actual duration/TSS
        parsed_data = parse_zwo_content(zwo_content, athlete_ftp)
        new_duration_min, new_tss = _extract_duration_tss_from_zwo(parsed_data["segments"], athlete_ftp)

        # Determine new workout type from description (simple heuristic)
        new_type = _infer_workout_type(workout_description)

        logger.info(f"Generated workout: type={new_type}, duration={new_duration_min}min, tss={new_tss}")

        # Delete old event from intervals.icu
        logger.info(f"Deleting old event {event_id} from intervals.icu")
        try:
            intervals_client.delete_event(event_id)
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TOOL_ERROR tool=modify_workout duration={duration_ms}ms error=Failed to delete event: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to delete old event from intervals.icu: {str(e)}"
            }

        # Create new event on intervals.icu
        logger.info("Creating new event on intervals.icu")
        filename = f"train-r-{date_str}.zwo"
        external_id = f"train-r-plan-{date_str}"

        # Get original scheduled time (or use 6 AM if not available)
        scheduled_time = f"{date_str}T06:00:00"

        try:
            upload_result = intervals_client.upload_workout_content(
                zwo_content=zwo_content,
                filename=filename,
                start_date=scheduled_time,
                external_id=external_id
            )
            new_event_id = upload_result.get("id")
            if not new_event_id:
                raise ValueError("No event ID returned from intervals.icu")
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TOOL_ERROR tool=modify_workout duration={duration_ms}ms error=Failed to create new event: {str(e)}")
            return {
                "success": False,
                "message": f"Deleted old event but failed to create new one: {str(e)}. Workout needs manual re-upload."
            }

        logger.info(f"Created new event with ID {new_event_id}")

        # Update current plan
        logger.info("Updating current plan")
        try:
            updated_workout = current_plan_service.update_workout(
                event_id=event_id,
                new_type=new_type,
                new_duration_min=new_duration_min,
                new_tss=new_tss,
                new_description=workout_description,
                user_prompt=workout_description,
                deleted_event_id=event_id,
                new_event_id=new_event_id
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TOOL_ERROR tool=modify_workout duration={duration_ms}ms error=Failed to update current plan: {str(e)}")
            return {
                "success": False,
                "message": f"Updated intervals.icu but failed to update local plan: {str(e)}"
            }

        # Log successful completion with timing
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(f"TOOL_END tool=modify_workout duration={duration_ms}ms success=True")

        return {
            "success": True,
            "date": date_str,
            "original_type": workout.get("original_type", workout.get("type")),
            "new_type": new_type,
            "deleted_event_id": event_id,
            "new_event_id": new_event_id,
            "message": f"Workout modified successfully for {date_str}"
        }

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"TOOL_ERROR tool=modify_workout duration={duration_ms}ms error={str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to modify workout: {str(e)}"
        }


def _validate_modify_params(
    event_id: int,
    current_plan_service: CurrentPlanService,
    intervals_client
) -> Tuple[bool, str, Optional[Tuple[str, dict]]]:
    """
    Validate modification parameters.

    Checks:
    - Event exists in current plan
    - Has intervals_event_id (was uploaded)
    - Date is >= today
    - Not completed (no paired_activity_id)

    Returns:
        (is_valid, error_message, workout_result)
    """
    # Check event exists in current plan
    workout_result = current_plan_service.get_workout_by_event_id(event_id)
    if not workout_result:
        return (False, f"Event ID {event_id} not found in training plan. This tool only modifies workouts from the active training plan.", None)

    date_str, workout = workout_result

    # Check date is in future
    try:
        workout_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        if workout_date < today:
            return (False, f"Cannot modify past workout from {date_str}. Only future workouts can be modified.", None)
    except ValueError:
        return (False, f"Invalid date format in workout: {date_str}", None)

    # Check not completed (by querying intervals.icu for this event)
    try:
        # Get planned events for this date
        planned_events = intervals_client.get_planned_events(
            oldest_date=date_str,
            newest_date=date_str
        )

        # Find our event
        for event in planned_events:
            if event.get("id") == event_id:
                if event.get("paired_activity_id"):
                    return (False, f"Cannot modify workout from {date_str} - it has already been completed. Would you like to create a new workout instead?", None)
                break
    except Exception as e:
        logger.warning(f"Could not verify completion status: {str(e)}")
        # Continue anyway - if we can't check, we'll allow the modification

    return (True, "", workout_result)


def _build_llm_prompt(workout: dict, new_description: str, athlete_ftp: int) -> str:
    """Build LLM prompt with context.

    Args:
        workout: Original workout dict
        new_description: New workout description from user
        athlete_ftp: Athlete's FTP

    Returns:
        Complete prompt for LLM
    """
    phase = workout.get("phase_name", "Training")
    week_tss = workout.get("week_target_tss", 0)
    week_hours = workout.get("week_target_hours", 0)
    original_desc = workout.get("description", "")

    prompt = f"""Modify workout for {phase} phase.
Week targets: {week_hours}h, {week_tss} TSS
Athlete FTP: {athlete_ftp}W

Original workout: {original_desc}

New workout request: {new_description}

Create a structured ZWO workout file based on the new description."""

    return prompt


def _extract_duration_tss_from_zwo(segments: list, athlete_ftp: int) -> Tuple[int, int]:
    """Extract duration and estimated TSS from ZWO segments.

    Args:
        segments: Parsed ZWO segments
        athlete_ftp: Athlete's FTP

    Returns:
        Tuple of (duration_minutes, estimated_tss)
    """
    total_seconds = sum(seg.get("duration_seconds", 0) for seg in segments)
    duration_min = int(total_seconds / 60)

    # Simple TSS estimation based on power and duration
    total_tss = 0
    for seg in segments:
        duration_hours = seg.get("duration_seconds", 0) / 3600
        power_pct = seg.get("power_pct_ftp", 50)
        intensity_factor = power_pct / 100
        # TSS = (duration_hours × IF² × 100)
        seg_tss = duration_hours * (intensity_factor ** 2) * 100
        total_tss += seg_tss

    return (duration_min, int(total_tss))


def _infer_workout_type(description: str) -> str:
    """Infer workout type from description using simple heuristics.

    Args:
        description: Workout description

    Returns:
        Workout type string
    """
    description_lower = description.lower()

    if "recovery" in description_lower or "easy" in description_lower:
        return "Recovery"
    elif "vo2" in description_lower or "vo2max" in description_lower:
        return "VO2 Max"
    elif "threshold" in description_lower or "ftp" in description_lower:
        return "Threshold"
    elif "sweet spot" in description_lower or "sweetspot" in description_lower:
        return "Sweet Spot"
    elif "tempo" in description_lower:
        return "Tempo"
    elif "endurance" in description_lower or "z2" in description_lower or "zone 2" in description_lower:
        return "Endurance"
    elif "sprint" in description_lower:
        return "Sprint"
    else:
        return "Endurance"  # Default
