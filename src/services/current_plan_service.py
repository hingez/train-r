"""Service for managing the current (modifiable) training plan.

This service handles initialization from the master plan, syncing with intervals.icu data,
and tracking workout modifications. It maintains a flattened date-keyed structure for
efficient lookups and modifications.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config import AppConfig

logger = logging.getLogger("train-r")


class CurrentPlanService:
    """Manages the current training plan with modification tracking."""

    def __init__(self, config: AppConfig):
        """Initialize current plan service paths.

        Args:
            config: Application configuration
        """
        self.config = config
        self.master_plan_path = config.data_dir / "plans" / "plan_v1.json"
        self.current_plan_dir = config.data_dir / "plans" / "current"
        self.active_plan_path = self.current_plan_dir / "active_plan.json"
        self.modifications_path = self.current_plan_dir / "modifications.json"
        self.sync_metadata_path = self.current_plan_dir / "sync_metadata.json"

        # Ensure directory exists
        self.current_plan_dir.mkdir(parents=True, exist_ok=True)

    def initialize_from_master(self) -> Dict:
        """Initialize current plan from master plan and intervals.icu sync data.

        This flattens the nested master plan structure (phases → weeks → days) into
        a date-keyed dictionary and maps event_ids from synced intervals data.

        Returns:
            Initialized current plan dict

        Raises:
            FileNotFoundError: If master plan file doesn't exist
            ValueError: If master plan structure is invalid
        """
        logger.info("Initializing current plan from master plan")

        # Load master plan
        if not self.master_plan_path.exists():
            raise FileNotFoundError(f"Master plan not found: {self.master_plan_path}")

        with open(self.master_plan_path, "r") as f:
            master_plan = json.load(f)

        # Validate master plan structure
        if "athlete_profile" not in master_plan or "ftp" not in master_plan["athlete_profile"]:
            raise ValueError("Master plan missing athlete_profile.ftp")
        if "training_plan" not in master_plan:
            raise ValueError("Master plan missing training_plan")

        athlete_ftp = master_plan["athlete_profile"]["ftp"]

        # Flatten master plan into date-keyed workouts
        workouts = self._flatten_master_plan(master_plan)

        # Create initial current plan structure
        current_plan = {
            "schema_version": "1.0",
            "initialized_from": "plan_v1.json",
            "initialized_at": datetime.now().isoformat(),
            "athlete_ftp": athlete_ftp,
            "last_intervals_sync": None,
            "workouts": workouts
        }

        # Save to active_plan.json
        with open(self.active_plan_path, "w") as f:
            json.dump(current_plan, f, indent=2)

        # Create empty modifications.json
        empty_modifications = {
            "schema_version": "1.0",
            "modifications": []
        }
        with open(self.modifications_path, "w") as f:
            json.dump(empty_modifications, f, indent=2)

        # Create sync_metadata.json
        sync_metadata = {
            "schema_version": "1.0",
            "initialized_at": datetime.now().isoformat(),
            "initialized_from_master": "plan_v1.json",
            "last_intervals_sync": None,
            "total_workouts": len(workouts),
            "modified_workouts_count": 0,
            "synced_event_ids": []
        }
        with open(self.sync_metadata_path, "w") as f:
            json.dump(sync_metadata, f, indent=2)

        logger.info(f"Initialized current plan with {len(workouts)} workouts")

        # Sync with intervals.icu data if available
        synced_count = self.sync_intervals_data()
        logger.info(f"Synced {synced_count} workouts with intervals.icu event IDs")

        return current_plan

    def _flatten_master_plan(self, master_plan: Dict) -> Dict[str, Dict]:
        """Flatten nested master plan into date-keyed workouts.

        Reuses logic from create_workout_plan_tool._generate_daily_summary()
        but returns a dict keyed by date instead of a list.

        Args:
            master_plan: Full nested plan from plan_v1.json

        Returns:
            Dict mapping date strings to workout dicts
        """
        workouts = {}
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        for phase in master_plan["training_plan"]:
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
                    date_str = workout_date.strftime("%Y-%m-%d")

                    workouts[date_str] = {
                        "date": date_str,
                        "workout_id": f"plan-{date_str}",
                        "day_name": day_name,
                        "iso_week": iso_week,
                        "phase_name": phase_name,
                        "type": workout["type"],
                        "duration_min": workout["duration_min"],
                        "tss": workout["tss"],
                        "description": workout["desc"],
                        "week_target_tss": target_tss,
                        "week_target_hours": target_hours,
                        "status": "unmodified",
                        "intervals_event_id": None,
                        "external_id": f"train-r-plan-{date_str}"
                    }

        return workouts

    def load_current_plan(self) -> Dict:
        """Load active_plan.json, auto-initialize if doesn't exist.

        Returns:
            Current plan dict with all workouts
        """
        if not self.active_plan_path.exists():
            logger.info("Active plan not found, initializing from master plan")
            return self.initialize_from_master()

        with open(self.active_plan_path, "r") as f:
            return json.load(f)

    def sync_intervals_data(self) -> int:
        """Sync event_ids from intervals.icu planned events data.

        Maps event_ids to workouts by matching start_date_local from
        data/athlete/raw/planned_events.json to workout dates in current plan.

        Returns:
            Number of workouts updated with event_ids
        """
        # Load current plan
        current_plan = self.load_current_plan()

        # Load intervals.icu planned events
        planned_events_path = self.config.athlete_data_dir / "raw" / "planned_events.json"
        if not planned_events_path.exists():
            logger.warning("No planned events data found, skipping event_id sync")
            return 0

        with open(planned_events_path, "r") as f:
            events_data = json.load(f)

        events = events_data.get("events", [])
        logger.info(f"Syncing with {len(events)} planned events from intervals.icu")

        # Map event_ids to dates
        synced_count = 0
        synced_event_ids = []

        for event in events:
            # Extract date from start_date_local (format: "YYYY-MM-DDTHH:MM:SS")
            start_date_local = event.get("start_date_local", "")
            if not start_date_local:
                continue

            date_str = start_date_local.split("T")[0]  # Extract YYYY-MM-DD

            # Check if this date exists in current plan
            if date_str in current_plan["workouts"]:
                event_id = event.get("id")
                external_id = event.get("external_id", "")

                # Only sync if external_id matches our pattern (train-r-plan-*)
                if external_id.startswith("train-r-plan-") and event_id:
                    current_plan["workouts"][date_str]["intervals_event_id"] = event_id
                    synced_count += 1
                    synced_event_ids.append(event_id)
                    logger.debug(f"Synced event_id {event_id} to date {date_str}")

        # Update last sync timestamp
        current_plan["last_intervals_sync"] = datetime.now().isoformat()

        # Save updated plan
        with open(self.active_plan_path, "w") as f:
            json.dump(current_plan, f, indent=2)

        # Update sync metadata
        if self.sync_metadata_path.exists():
            with open(self.sync_metadata_path, "r") as f:
                sync_metadata = json.load(f)

            sync_metadata["last_intervals_sync"] = datetime.now().isoformat()
            sync_metadata["synced_event_ids"] = synced_event_ids

            with open(self.sync_metadata_path, "w") as f:
                json.dump(sync_metadata, f, indent=2)

        logger.info(f"Synced {synced_count} workouts with intervals.icu event IDs")
        return synced_count

    def get_workout_by_event_id(self, event_id: int) -> Optional[Tuple[str, Dict]]:
        """Retrieve workout by intervals.icu event_id.

        Args:
            event_id: intervals.icu event ID

        Returns:
            Tuple of (date_str, workout_dict) or None if not found
        """
        current_plan = self.load_current_plan()

        for date_str, workout in current_plan["workouts"].items():
            if workout.get("intervals_event_id") == event_id:
                return (date_str, workout)

        return None

    def get_workout_by_date(self, date: str) -> Optional[Dict]:
        """Retrieve workout by date (YYYY-MM-DD).

        Args:
            date: Date string in YYYY-MM-DD format

        Returns:
            Workout dict or None if not found
        """
        current_plan = self.load_current_plan()
        return current_plan["workouts"].get(date)

    def update_workout(
        self,
        event_id: int,
        new_type: str,
        new_duration_min: int,
        new_tss: int,
        new_description: str,
        user_prompt: str,
        deleted_event_id: int,
        new_event_id: int
    ) -> Dict:
        """Update workout in current plan after modification.

        Preserves original values on first modification and appends to audit trail.

        Args:
            event_id: Original event_id to find the workout
            new_type: New workout type
            new_duration_min: New duration in minutes
            new_tss: New TSS value
            new_description: New workout description
            user_prompt: User's modification request
            deleted_event_id: Old event_id that was deleted
            new_event_id: New event_id from intervals.icu

        Returns:
            Updated workout dict

        Raises:
            ValueError: If workout not found by event_id
        """
        current_plan = self.load_current_plan()

        # Find workout by event_id
        workout_result = self.get_workout_by_event_id(event_id)
        if not workout_result:
            raise ValueError(f"Workout not found with event_id {event_id}")

        date_str, workout = workout_result

        # Preserve original values if first modification
        if workout["status"] == "unmodified":
            workout["original_type"] = workout["type"]
            workout["original_duration_min"] = workout["duration_min"]
            workout["original_tss"] = workout["tss"]
            workout["original_description"] = workout["description"]

        # Update workout fields
        workout["type"] = new_type
        workout["duration_min"] = new_duration_min
        workout["tss"] = new_tss
        workout["description"] = new_description
        workout["status"] = "modified"
        workout["modified_at"] = datetime.now().isoformat()
        workout["intervals_event_id"] = new_event_id

        # Generate modification ID
        modification_id = self._generate_modification_id()
        workout["modification_id"] = modification_id

        # Save updated current plan
        with open(self.active_plan_path, "w") as f:
            json.dump(current_plan, f, indent=2)

        # Append to modifications audit trail
        self._append_modification(
            modification_id=modification_id,
            date=date_str,
            deleted_event_id=deleted_event_id,
            new_event_id=new_event_id,
            user_prompt=user_prompt,
            changes={
                "type": {"from": workout.get("original_type"), "to": new_type},
                "duration_min": {"from": workout.get("original_duration_min"), "to": new_duration_min},
                "tss": {"from": workout.get("original_tss"), "to": new_tss},
                "description": {"from": workout.get("original_description"), "to": new_description}
            }
        )

        # Update sync metadata
        self._update_modified_count()

        logger.info(f"Updated workout for date {date_str} (modification_id: {modification_id})")

        return workout

    def _generate_modification_id(self) -> str:
        """Generate unique modification ID.

        Returns:
            Modification ID in format: mod-YYYYMMDD-HHMMSS
        """
        return f"mod-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def _append_modification(
        self,
        modification_id: str,
        date: str,
        deleted_event_id: int,
        new_event_id: int,
        user_prompt: str,
        changes: Dict
    ):
        """Append modification to audit trail.

        Args:
            modification_id: Unique modification ID
            date: Workout date
            deleted_event_id: Old event_id that was deleted
            new_event_id: New event_id from intervals.icu
            user_prompt: User's modification request
            changes: Dict of before/after values
        """
        # Load modifications file
        if self.modifications_path.exists():
            with open(self.modifications_path, "r") as f:
                modifications_data = json.load(f)
        else:
            modifications_data = {
                "schema_version": "1.0",
                "modifications": []
            }

        # Append new modification
        modification_entry = {
            "modification_id": modification_id,
            "date": date,
            "intervals_event_id": deleted_event_id,
            "timestamp": datetime.now().isoformat(),
            "action": "modify_workout",
            "changes": changes,
            "intervals_deleted_event_id": deleted_event_id,
            "intervals_new_event_id": new_event_id,
            "user_prompt": user_prompt
        }

        modifications_data["modifications"].append(modification_entry)

        # Save updated modifications
        with open(self.modifications_path, "w") as f:
            json.dump(modifications_data, f, indent=2)

        logger.info(f"Appended modification {modification_id} to audit trail")

    def _update_modified_count(self):
        """Update modified workouts count in sync metadata."""
        if not self.sync_metadata_path.exists():
            return

        with open(self.sync_metadata_path, "r") as f:
            sync_metadata = json.load(f)

        # Count modified workouts
        current_plan = self.load_current_plan()
        modified_count = sum(
            1 for workout in current_plan["workouts"].values()
            if workout["status"] == "modified"
        )

        sync_metadata["modified_workouts_count"] = modified_count

        with open(self.sync_metadata_path, "w") as f:
            json.dump(sync_metadata, f, indent=2)

    def get_modifications_audit(self) -> List[Dict]:
        """Return full modification history.

        Returns:
            List of modification entries
        """
        if not self.modifications_path.exists():
            return []

        with open(self.modifications_path, "r") as f:
            modifications_data = json.load(f)

        return modifications_data.get("modifications", [])
