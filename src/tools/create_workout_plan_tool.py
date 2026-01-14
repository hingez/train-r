"""Tool for creating comprehensive multi-week training plans."""
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from src.config import AppConfig

if TYPE_CHECKING:
    from src.services.coach_service import CoachService

logger = logging.getLogger("train-r")


def execute(args: dict, config: AppConfig, coach_service: "CoachService" = None) -> dict:
    """
    Execute workout plan creation with 15-second mock delay.

    Args:
        args: {"athlete_ftp": int, "goal_description": str}
        config: AppConfig instance
        coach_service: CoachService instance

    Returns:
        {
            "success": True,
            "message": "Training plan created and ready for review",
            "plan": <full nested plan>,
            "summarized": <flat daily list>,
            "total_weeks": 24,
            "total_workouts": 168
        }
    """
    # Log tool start and begin timing
    logger.info(f"TOOL_START tool=create_workout_plan args={args}")
    start_time = time.time()

    try:
        # Extract parameters
        athlete_ftp = args.get("athlete_ftp")
        goal_description = args.get("goal_description", "General fitness improvement")

        # Validate FTP
        if not athlete_ftp or not isinstance(athlete_ftp, int):
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TOOL_ERROR tool=create_workout_plan duration={duration_ms}ms error=athlete_ftp validation failed")
            return {
                "success": False,
                "message": "athlete_ftp is required and must be an integer"
            }

        if athlete_ftp < 100 or athlete_ftp > 500:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TOOL_ERROR tool=create_workout_plan duration={duration_ms}ms error=athlete_ftp out of range")
            return {
                "success": False,
                "message": f"athlete_ftp must be between 100 and 500 watts (got {athlete_ftp})"
            }

        logger.info(f"Creating training plan for FTP={athlete_ftp}W, goal={goal_description}")

        # Mock LLM delay (15 seconds)
        logger.info("Simulating LLM processing (15 second delay)...")
        time.sleep(15)

        # Load mock plan data
        plan_path = Path(config.project_root) / "data" / "plans" / "plan_v1.json"
        if not plan_path.exists():
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"TOOL_ERROR tool=create_workout_plan duration={duration_ms}ms error=Plan file not found")
            return {
                "success": False,
                "message": f"Mock plan file not found at {plan_path}"
            }

        with open(plan_path, "r") as f:
            plan_data = json.load(f)

        logger.info("Loaded mock plan data")

        # Generate summarized daily view
        summarized_data = _generate_daily_summary(plan_data)

        # Save summarized data
        summary_path = Path(config.project_root) / "data" / "plans" / "summarized_plan.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, "w") as f:
            json.dump(summarized_data, f, indent=2)

        logger.info(f"Saved summarized plan to {summary_path}")

        # Calculate statistics
        total_weeks = sum(len(phase["weeks"]) for phase in plan_data["training_plan"])
        total_workouts = len(summarized_data)

        # Log successful completion with timing
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(f"TOOL_END tool=create_workout_plan duration={duration_ms}ms success=True")

        return {
            "success": True,
            "message": "Training plan created and ready for review",
            "plan": plan_data,
            "summarized": summarized_data,
            "total_weeks": total_weeks,
            "total_workouts": total_workouts
        }

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"TOOL_ERROR tool=create_workout_plan duration={duration_ms}ms error={str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to create training plan: {str(e)}"
        }


def _generate_daily_summary(plan_data: dict) -> list[dict]:
    """
    Transform nested plan structure into flat daily list.

    Args:
        plan_data: Full nested plan from plan_v1.json

    Returns:
        List of daily workout dictionaries with date, type, tss, etc.
    """
    daily_workouts = []
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    for phase in plan_data["training_plan"]:
        phase_name = phase["phase_name"]

        for week in phase["weeks"]:
            iso_week = week["iso_week"]
            start_date_str = week["start_date"]
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            target_hours = week["target_hours"]
            target_tss = week["target_tss"]
            schedule = week["schedule"]

            for day_idx, day_name in enumerate(day_names):
                workout = schedule[day_name]
                workout_date = start_date + timedelta(days=day_idx)

                daily_workouts.append({
                    "date": workout_date.strftime("%Y-%m-%d"),
                    "day_name": day_name.capitalize(),
                    "iso_week": iso_week,
                    "phase_name": phase_name,
                    "type": workout["type"],
                    "duration_min": workout["duration_min"],
                    "tss": workout["tss"],
                    "description": workout["desc"],
                    "week_target_hours": target_hours,
                    "week_target_tss": target_tss
                })

    return daily_workouts
