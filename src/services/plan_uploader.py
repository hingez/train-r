"""Service for uploading training plan workouts to intervals.icu.

This service extracts the core upload logic from the standalone script
and makes it callable from the main application with progress callbacks.
"""

import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.config import AppConfig
from src.integrations.intervals import IntervalsClient
from src.utils.retry import retry_with_backoff
from src.utils.workout_generator import WorkoutGenerator

logger = logging.getLogger('train-r')


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


class PlanUploaderService:
    """Service for uploading training plan workouts to intervals.icu."""

    def __init__(
        self,
        workout_gen: WorkoutGenerator,
        intervals_client: IntervalsClient,
        config: AppConfig
    ):
        """Initialize uploader service.

        Args:
            workout_gen: WorkoutGenerator instance for generating ZWO files
            intervals_client: IntervalsClient for uploading to intervals.icu
            config: Application configuration
        """
        self.workout_gen = workout_gen
        self.intervals_client = intervals_client
        self.config = config
        self.checkpoint_file = config.data_dir / "upload_checkpoint.json"
        self.plan_file = config.data_dir / "plans" / "plan_v1.json"

    def load_and_filter_workouts(
        self,
        max_workouts: int
    ) -> tuple[List[WorkoutTask], int]:
        """Load plan and extract future workouts.

        Args:
            max_workouts: Maximum number of future workouts to process

        Returns:
            Tuple of (workout tasks list, athlete FTP)
        """
        if not self.plan_file.exists():
            raise FileNotFoundError(f"Plan file not found: {self.plan_file}")

        # Load plan JSON
        with open(self.plan_file, 'r') as f:
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

    def build_llm_prompt(self, task: WorkoutTask, athlete_ftp: int) -> Optional[str]:
        """Construct LLM prompt from plan data.

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

    def load_checkpoint(self) -> Dict:
        """Load checkpoint file or create new one."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Corrupted checkpoint file, starting fresh")

        return {
            "last_updated": None,
            "athlete_ftp": None,
            "plan_file": str(self.plan_file),
            "uploaded_dates": [],
            "workouts": []
        }

    def save_checkpoint(self, checkpoint: Dict):
        """Save checkpoint to file."""
        checkpoint["last_updated"] = datetime.now().isoformat()

        # Ensure directory exists
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

    def update_checkpoint(
        self,
        checkpoint: Dict,
        date: str,
        event_id: int,
        external_id: str,
        workout_type: str
    ):
        """Update checkpoint with uploaded workout.

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
        self,
        task: WorkoutTask,
        athlete_ftp: int,
        checkpoint: Dict,
        checkpoint_lock: threading.Lock,
        session_id: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Worker function to generate and upload one workout.

        Args:
            task: Workout task to process
            athlete_ftp: Athlete FTP
            checkpoint: Checkpoint dictionary
            checkpoint_lock: Lock for thread-safe checkpoint updates
            session_id: LangSmith session ID
            progress_callback: Optional callback(date, success) called after upload

        Returns:
            Result dictionary with success status and metadata
        """
        try:
            # Build workout description (from plan_v1.json)
            prompt = self.build_llm_prompt(task, athlete_ftp)
            if not prompt:  # Skip Rest days
                logger.info(f"Skipping rest day: {task.date}")
                return {"skipped": True, "reason": "Rest day", "date": task.date}

            # Generate ZWO using LLM (with 5 retries + LangSmith tracing)
            logger.info(f"Generating workout for {task.date} ({task.workout_type})")
            zwo_content = retry_with_backoff(
                func=lambda: self.workout_gen.generate_workout(
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
            result = self.intervals_client.upload_workout_content(
                zwo_content=zwo_content,
                filename=filename,
                start_date=scheduled_time,
                external_id=external_id
            )

            event_id = result.get("id") if isinstance(result, dict) else None

            # Update checkpoint (thread-safe)
            with checkpoint_lock:
                self.update_checkpoint(checkpoint, task.date, event_id, external_id, task.workout_type)
                self.save_checkpoint(checkpoint)

            logger.info(f"Successfully uploaded workout for {task.date} (event_id: {event_id})")

            # Call progress callback if provided
            if progress_callback:
                try:
                    progress_callback(task.date, True)
                except Exception as e:
                    logger.error(f"Progress callback error: {e}")

            return {
                "success": True,
                "date": task.date,
                "event_id": event_id,
                "workout_type": task.workout_type
            }

        except Exception as e:
            logger.error(f"Failed to process workout {task.date} after 5 retries: {e}", exc_info=True)

            # Call progress callback for failed workout
            if progress_callback:
                try:
                    progress_callback(task.date, False)
                except Exception as callback_error:
                    logger.error(f"Progress callback error: {callback_error}")

            return {
                "success": False,
                "date": task.date,
                "error": str(e),
                "workout_type": task.workout_type
            }

    def upload_pending_workouts(
        self,
        max_workouts: int = 14,
        progress_callback: Optional[Callable[[str, bool], None]] = None
    ) -> Dict:
        """Upload pending workouts with optional progress callbacks.

        This is the main entry point for uploading workouts. It can be called
        synchronously from a thread pool.

        Args:
            max_workouts: Maximum number of future workouts to upload
            progress_callback: Optional sync function called with (workout_date, success)
                               after each workout upload

        Returns:
            Upload summary dict with success/skip/fail counts
        """
        try:
            # Load and filter workouts
            workouts, athlete_ftp = self.load_and_filter_workouts(max_workouts)
            logger.info(f"Found {len(workouts)} future workouts to process")

            if not workouts:
                logger.warning("No future workouts found")
                return {"success": 0, "skipped": 0, "failed": 0, "total": 0}

            # Load checkpoint
            checkpoint = self.load_checkpoint()
            checkpoint["athlete_ftp"] = athlete_ftp
            checkpoint["plan_file"] = str(self.plan_file)

            # Filter already uploaded
            pending = [
                w for w in workouts
                if w.date not in checkpoint["uploaded_dates"]
            ]

            already_uploaded = len(workouts) - len(pending)
            logger.info(f"Uploading {len(pending)} workouts ({already_uploaded} already uploaded)")

            if not pending:
                logger.info("All workouts already uploaded!")
                return {"success": 0, "skipped": already_uploaded, "failed": 0, "total": len(workouts)}

            # Generate session ID for LangSmith tracing
            session_id = f"plan-upload-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"LangSmith session ID: {session_id}")

            # Process concurrently with 5 workers
            checkpoint_lock = threading.Lock()
            results = []

            with ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all tasks
                futures = {
                    executor.submit(
                        self.process_workout,
                        task,
                        athlete_ftp,
                        checkpoint,
                        checkpoint_lock,
                        session_id,
                        progress_callback
                    ): task
                    for task in pending
                }

                # Collect results
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)

            # Calculate summary
            success_count = sum(1 for r in results if r.get("success"))
            skip_count = sum(1 for r in results if r.get("skipped")) + already_uploaded
            fail_count = len(results) - sum(1 for r in results if r.get("success") or r.get("skipped"))

            summary = {
                "success": success_count,
                "skipped": skip_count,
                "failed": fail_count,
                "total": len(workouts)
            }

            logger.info(f"Upload complete: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Upload failed: {e}", exc_info=True)
            raise
