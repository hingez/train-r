#!/usr/bin/env python3
"""Upload training plan workouts to intervals.icu using concurrent processing.

This script loads a training plan from JSON, filters future workouts, and uploads
them to intervals.icu using LLM-generated ZWO files. Features concurrent processing,
retry logic, checkpoint-based resumption, and LangSmith tracing.

IMPORTANT: This script is primarily for MANUAL OVERWRITES of existing workouts.
The main Train-R application automatically uploads workouts in the background on
startup, so you typically don't need to run this script unless you want to:

1. Force re-upload workouts with updated data (e.g., after changing FTP)
2. Upload more than the default 2 weeks of workouts
3. Manually retry failed uploads

To force re-upload workouts:
    # Option 1: Delete the entire checkpoint file to re-upload all workouts
    rm data/upload_checkpoint.json
    uv run python scripts/upload_plan_to_intervals.py --max-workouts 14

    # Option 2: Edit the checkpoint file to remove specific dates from "uploaded_dates"
    # Then run the script - it will only upload the removed dates

The script uses intervals.icu's upsert mode, so re-uploading will automatically
overwrite existing workouts with the same external_id (train-r-plan-YYYY-MM-DD).

Usage:
    uv run python scripts/upload_plan_to_intervals.py --max-workouts 20
    uv run python scripts/upload_plan_to_intervals.py --max-workouts 10 --dry-run
"""

import argparse
import json
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import AppConfig
from src.integrations.intervals import IntervalsClient
from src.integrations.llm_client import LLMClient
from src.utils.logger import setup_logger
from src.utils.retry import retry_with_backoff
from src.utils.workout_generator import WorkoutGenerator

# Setup logger
logger = setup_logger()


@dataclass
class WorkoutTask:
    """Represents a single workout to be uploaded."""

    date: str  # YYYY-MM-DD
    day_name: str  # e.g., "wednesday"
    workout_type: str  # e.g., "Sweet Spot"
    duration_min: int
    tss: int
    description: str  # From plan 'desc' field
    phase_name: str
    week_target_tss: int
    iso_week: int


def load_and_filter_workouts(
    plan_file: Path,
    max_workouts: int
) -> tuple[List[WorkoutTask], int]:
    """Load plan and extract future workouts.

    Args:
        plan_file: Path to plan JSON file
        max_workouts: Maximum number of future workouts to process

    Returns:
        Tuple of (workout tasks list, athlete FTP)

    Raises:
        FileNotFoundError: If plan file doesn't exist
        ValueError: If plan structure is invalid
    """
    if not plan_file.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_file}")

    # Load plan JSON
    with open(plan_file, 'r') as f:
        plan = json.load(f)

    # Validate structure
    if "athlete_profile" not in plan or "ftp" not in plan["athlete_profile"]:
        raise ValueError("Plan missing athlete_profile.ftp")
    if "training_plan" not in plan:
        raise ValueError("Plan missing training_plan")

    athlete_ftp = plan["athlete_profile"]["ftp"]

    # Day name to offset mapping
    day_offsets = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    # Flatten nested structure (phases → weeks → days)
    all_workouts = []
    for phase in plan["training_plan"]:
        phase_name = phase.get("phase_name", "Unknown Phase")

        for week in phase.get("weeks", []):
            iso_week = week.get("iso_week")
            week_start_str = week.get("start_date")
            week_target_tss = week.get("target_tss", 0)

            if not week_start_str:
                logger.warning(f"Week in {phase_name} missing start_date, skipping")
                continue

            week_start = datetime.fromisoformat(week_start_str).date()

            for day_name, workout in week.get("schedule", {}).items():
                # Calculate actual date (Monday + day offset)
                day_offset = day_offsets.get(day_name.lower())
                if day_offset is None:
                    logger.warning(f"Unknown day name: {day_name}, skipping")
                    continue

                workout_date = week_start + timedelta(days=day_offset)

                all_workouts.append(WorkoutTask(
                    date=workout_date.strftime("%Y-%m-%d"),
                    day_name=day_name,
                    workout_type=workout.get("type", "Unknown"),
                    duration_min=workout.get("duration_min", 0),
                    tss=workout.get("tss", 0),
                    description=workout.get("desc", ""),
                    phase_name=phase_name,
                    week_target_tss=week_target_tss,
                    iso_week=iso_week or 0
                ))

    # Filter and limit
    today = datetime.now().date()
    future_workouts = [
        w for w in all_workouts
        if datetime.fromisoformat(w.date).date() >= today
    ]

    # Sort by date
    future_workouts.sort(key=lambda w: w.date)

    return future_workouts[:max_workouts], athlete_ftp


def build_llm_prompt(task: WorkoutTask, athlete_ftp: int) -> Optional[str]:
    """Construct LLM prompt from plan data.

    Uses the workout description from plan_v1.json (the 'desc' field)
    along with phase context to help LLM understand progression.

    This is sent as the USER MESSAGE to the LLM, with the system prompt
    being the workout_generator_prompt.txt template.

    Args:
        task: Workout task with plan data
        athlete_ftp: Athlete's FTP in watts

    Returns:
        Prompt string or None if rest day
    """
    # Skip Rest days (duration = 0)
    if task.duration_min == 0:
        return None

    # This becomes the user message - includes description from plan
    return (
        f"Training Phase: {task.phase_name}\n"
        f"Workout Type: {task.workout_type}\n"
        f"Duration: {task.duration_min} minutes\n"
        f"Target TSS: {task.tss}\n"
        f"Athlete FTP: {athlete_ftp}W\n\n"
        f"Workout Details:\n{task.description}"
    )


def load_checkpoint(checkpoint_file: Path) -> Dict:
    """Load checkpoint file or create new one.

    Args:
        checkpoint_file: Path to checkpoint JSON

    Returns:
        Checkpoint dictionary
    """
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Corrupted checkpoint file, starting fresh")

    return {
        "last_updated": None,
        "athlete_ftp": None,
        "plan_file": None,
        "uploaded_dates": [],
        "workouts": []
    }


def save_checkpoint(checkpoint_file: Path, checkpoint: Dict):
    """Save checkpoint to file.

    Args:
        checkpoint_file: Path to checkpoint JSON
        checkpoint: Checkpoint data
    """
    checkpoint["last_updated"] = datetime.now().isoformat()

    # Ensure directory exists
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def update_checkpoint(
    checkpoint: Dict,
    date: str,
    event_id: int,
    external_id: str,
    workout_type: str
):
    """Update checkpoint with uploaded workout (NOT thread-safe alone).

    Caller must hold checkpoint_lock when calling this.

    Args:
        checkpoint: Checkpoint dictionary
        date: Workout date (YYYY-MM-DD)
        event_id: intervals.icu event ID
        external_id: External tracking ID
        workout_type: Type of workout
    """
    checkpoint["workouts"].append({
        "date": date,
        "event_id": event_id,
        "external_id": external_id,
        "workout_type": workout_type,
        "uploaded_at": datetime.now().isoformat()
    })

    if date not in checkpoint["uploaded_dates"]:
        checkpoint["uploaded_dates"].append(date)


def process_workout(
    task: WorkoutTask,
    athlete_ftp: int,
    workout_gen: WorkoutGenerator,
    intervals_client: IntervalsClient,
    checkpoint: Dict,
    checkpoint_lock: threading.Lock,
    checkpoint_file: Path,
    session_id: str
) -> Dict:
    """Worker function to generate and upload one workout.

    Thread-safe via checkpoint_lock for state updates.

    Args:
        task: Workout task to process
        athlete_ftp: Athlete FTP
        workout_gen: WorkoutGenerator instance
        intervals_client: IntervalsClient instance
        checkpoint: Checkpoint dictionary
        checkpoint_lock: Lock for thread-safe checkpoint updates
        checkpoint_file: Path to checkpoint file
        session_id: LangSmith session ID

    Returns:
        Result dictionary with success status and metadata
    """
    try:
        # Build workout description (from plan_v1.json)
        prompt = build_llm_prompt(task, athlete_ftp)
        if not prompt:  # Skip Rest days
            logger.info(f"Skipping rest day: {task.date}")
            return {"skipped": True, "reason": "Rest day", "date": task.date}

        # Generate ZWO using LLM (with 5 retries + LangSmith tracing)
        logger.info(f"Generating workout for {task.date} ({task.workout_type})")
        zwo_content = retry_with_backoff(
            func=lambda: workout_gen.generate_workout(
                workout_description=prompt,
                session_id=session_id
            ),
            exception_types=(Exception,),
            operation_name=f"Generate workout {task.date}",
            max_retries=5
        )

        # Construct filename and metadata
        timestamp = task.date.replace("-", "") + "_120000"  # Noon timestamp
        filename = f"{timestamp}.zwo"
        external_id = f"train-r-plan-{task.date}"
        scheduled_time = f"{task.date}T12:00:00"  # Noon scheduling

        # Upload to intervals.icu (already has retry built-in + upsert)
        logger.info(f"Uploading workout for {task.date} to intervals.icu")
        result = intervals_client.upload_workout_content(
            zwo_content=zwo_content,
            filename=filename,
            start_date=scheduled_time,
            external_id=external_id
        )

        event_id = result.get("id") if isinstance(result, dict) else None

        # Update checkpoint (thread-safe)
        with checkpoint_lock:
            update_checkpoint(checkpoint, task.date, event_id, external_id, task.workout_type)
            save_checkpoint(checkpoint_file, checkpoint)

        logger.info(f"Successfully uploaded workout for {task.date} (event_id: {event_id})")

        return {
            "success": True,
            "date": task.date,
            "event_id": event_id,
            "workout_type": task.workout_type
        }

    except Exception as e:
        logger.error(f"Failed to process workout {task.date} after 5 retries: {e}", exc_info=True)
        return {
            "success": False,
            "date": task.date,
            "error": str(e),
            "workout_type": task.workout_type
        }


def print_workout_preview(workouts: List[WorkoutTask]):
    """Print preview of workouts to be uploaded.

    Args:
        workouts: List of workout tasks
    """
    print("\n" + "=" * 80)
    print(f"PREVIEW: {len(workouts)} workouts to upload")
    print("=" * 80)

    for i, w in enumerate(workouts, 1):
        rest_indicator = " [REST]" if w.duration_min == 0 else ""
        print(f"{i:3d}. {w.date} ({w.day_name:9s}) - {w.workout_type:20s} "
              f"({w.duration_min:3d}min, {w.tss:3d} TSS){rest_indicator}")
        if w.duration_min > 0:
            print(f"      Phase: {w.phase_name}")
            print(f"      Desc: {w.description[:70]}...")

    print("=" * 80 + "\n")


def main():
    """Main entry point for upload script."""
    parser = argparse.ArgumentParser(
        description="Upload training plan workouts to intervals.icu",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload next 10 workouts
  python scripts/upload_plan_to_intervals.py --max-workouts 10

  # Preview without uploading
  python scripts/upload_plan_to_intervals.py --max-workouts 20 --dry-run

  # Custom plan file
  python scripts/upload_plan_to_intervals.py --plan-file data/plans/custom.json --max-workouts 5
        """
    )

    parser.add_argument(
        "--plan-file",
        type=Path,
        default=project_root / "data" / "plans" / "plan_v1.json",
        help="Path to plan JSON file (default: data/plans/plan_v1.json)"
    )
    parser.add_argument(
        "--max-workouts",
        type=int,
        required=True,
        help="Number of future workouts to upload (required)"
    )
    parser.add_argument(
        "--checkpoint-file",
        type=Path,
        default=project_root / "data" / "upload_checkpoint.json",
        help="Path to checkpoint file (default: data/upload_checkpoint.json)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview workouts without generating or uploading"
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("Training Plan Upload Script")
    logger.info("=" * 80)

    try:
        # Load and filter workouts
        logger.info(f"Loading plan from: {args.plan_file}")
        workouts, athlete_ftp = load_and_filter_workouts(args.plan_file, args.max_workouts)
        logger.info(f"Found {len(workouts)} future workouts to process")
        logger.info(f"Athlete FTP: {athlete_ftp}W")

        if not workouts:
            logger.warning("No future workouts found")
            return

        # Load checkpoint
        checkpoint = load_checkpoint(args.checkpoint_file)
        checkpoint["athlete_ftp"] = athlete_ftp
        checkpoint["plan_file"] = str(args.plan_file)

        # Filter already uploaded
        pending = [
            w for w in workouts
            if w.date not in checkpoint["uploaded_dates"]
        ]

        already_uploaded = len(workouts) - len(pending)
        logger.info(f"Uploading {len(pending)} workouts ({already_uploaded} already uploaded)")

        if args.dry_run:
            print_workout_preview(pending)
            logger.info("Dry run complete - no workouts uploaded")
            return

        if not pending:
            logger.info("All workouts already uploaded!")
            return

        # Initialize services (single instances shared across threads)
        logger.info("Initializing services...")
        config = AppConfig.from_env()

        llm_client = LLMClient(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            langsmith_tracing_enabled=config.langsmith_tracing_enabled,
            langsmith_api_key=config.langsmith_api_key,
            langsmith_project=config.langsmith_project
        )
        workout_gen = WorkoutGenerator(llm_client, config)
        intervals_client = IntervalsClient(config.intervals_api_key, config)
        checkpoint_lock = threading.Lock()

        # Generate session ID for LangSmith tracing (groups all uploads)
        session_id = f"plan-upload-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"LangSmith session ID: {session_id}")

        # Process concurrently with 5 workers
        logger.info("Starting concurrent upload with 5 workers...")
        results = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks (pass session_id for LangSmith tracing)
            futures = {
                executor.submit(
                    process_workout,
                    task,
                    athlete_ftp,
                    workout_gen,
                    intervals_client,
                    checkpoint,
                    checkpoint_lock,
                    args.checkpoint_file,
                    session_id
                ): task
                for task in pending
            }

            # Collect results with progress tracking
            for i, future in enumerate(as_completed(futures), 1):
                result = future.result()
                results.append(result)

                # Progress logging
                if result.get("skipped"):
                    status = "⊘"
                    reason = result.get("reason", "Unknown")
                    logger.info(f"[{i}/{len(pending)}] {status} {result.get('date')} - Skipped ({reason})")
                elif result.get("success"):
                    status = "✓"
                    logger.info(f"[{i}/{len(pending)}] {status} {result.get('date')} - {result.get('workout_type')}")
                else:
                    status = "✗"
                    error = result.get("error", "Unknown error")
                    logger.error(f"[{i}/{len(pending)}] {status} {result.get('date')} - FAILED: {error}")

        # Summary
        success_count = sum(1 for r in results if r.get("success"))
        skip_count = sum(1 for r in results if r.get("skipped"))
        fail_count = len(results) - success_count - skip_count

        logger.info("=" * 80)
        logger.info(f"Upload complete: {success_count} successful, {skip_count} skipped, {fail_count} failed")
        logger.info(f"Checkpoint saved to: {args.checkpoint_file}")
        logger.info("=" * 80)

        if fail_count > 0:
            logger.warning(f"{fail_count} workouts failed - check logs for details")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Script failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
