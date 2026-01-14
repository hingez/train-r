"""Data synchronization service for athlete data from intervals.icu.

This module handles incremental syncing of workout history, planned events,
power curves, and workout matching from intervals.icu API.
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from collections import defaultdict

from src.config import AppConfig
from src.integrations.intervals import IntervalsClient
from src.services.workout_matcher import match_workouts
from src.services.index_builder import build_workout_index

logger = logging.getLogger('train-r')


def load_sync_metadata(config: AppConfig) -> Optional[dict]:
    """Load sync metadata from JSON file.

    Args:
        config: Application configuration

    Returns:
        Metadata dict or None if file doesn't exist
    """
    metadata_path = config.athlete_data_dir / "sync_metadata.json"

    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading sync metadata: {e}")
        return None


def save_sync_metadata(metadata: dict, config: AppConfig):
    """Save sync metadata to JSON file.

    Args:
        metadata: Metadata dictionary to save
        config: Application configuration
    """
    metadata_path = config.athlete_data_dir / "sync_metadata.json"

    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving sync metadata: {e}")


def get_last_activity_date(metadata: Optional[dict]) -> Optional[str]:
    """Extract last activity date from metadata.

    Args:
        metadata: Sync metadata dictionary

    Returns:
        Last activity date string in YYYY-MM-DD format, or None
    """
    if not metadata:
        return None

    return metadata.get("last_activity_date")


def get_last_event_date(metadata: Optional[dict]) -> Optional[str]:
    """Extract last event date from metadata.

    Args:
        metadata: Sync metadata dictionary

    Returns:
        Last event date string in YYYY-MM-DD format, or None
    """
    if not metadata:
        return None

    return metadata.get("last_event_date")


def should_do_full_sync(metadata: Optional[dict]) -> bool:
    """Determine if a full sync is needed.

    Args:
        metadata: Sync metadata dictionary

    Returns:
        True if full sync needed, False for incremental
    """
    if not metadata:
        return True

    # If no last sync timestamp, do full sync
    if not metadata.get("last_sync_timestamp"):
        return True

    # If no last activity date, do full sync
    if not metadata.get("last_activity_date"):
        return True

    return False


class DataSyncService:
    """Service for syncing athlete data from intervals.icu with incremental updates."""

    def __init__(self, intervals_client: IntervalsClient, config: AppConfig):
        """Initialize data sync service.

        Args:
            intervals_client: Initialized intervals.icu client
            config: Application configuration
        """
        self.intervals_client = intervals_client
        self.config = config

    def sync_athlete_data(self, force_full: bool = False, skip_power_curves: bool = False) -> dict:
        """Main sync function - syncs workout history, planned events, power curves.

        Args:
            force_full: If True, force a full sync instead of incremental
            skip_power_curves: If True, skip fetching power curves for faster sync

        Returns:
            Summary dict with sync stats
        """
        logger.info("=" * 60)
        logger.info("Starting athlete data sync (synchronous)")
        logger.info("=" * 60)

        # Load existing metadata
        metadata = load_sync_metadata(self.config)

        # Determine sync strategy
        do_full = force_full or should_do_full_sync(metadata)

        # Phase 1: Fetch completed activities
        if do_full:
            logger.info(f"Performing FULL sync ({self.config.history_initial_lookback_days // 365} years of data)")
            activities = self._fetch_full_activities()
        else:
            logger.info("Performing INCREMENTAL sync (new activities only)")
            last_date = get_last_activity_date(metadata)
            new_activities = self._fetch_incremental_activities(last_date)

            # Merge with existing data
            existing_activities = self._load_existing_activities()
            activities = self._merge_activities(existing_activities, new_activities)
            logger.info(f"Merged {len(new_activities)} new activities with {len(existing_activities)} existing = {len(activities)} total")

        # Phase 2: Fetch planned events
        logger.info("Fetching planned events")
        events = self._fetch_planned_events(metadata, do_full)

        # Phase 3: Fetch power curves (or use cached if skipped)
        if skip_power_curves:
            logger.info("Using cached power curves (skipped for speed)")
            power_curves = self._load_existing_power_curves()
        else:
            logger.info("Fetching fresh power curves from intervals.icu")
            power_curves = self._fetch_power_curves()

        # Phase 4: Match planned vs actual
        logger.info("Matching planned events with completed activities")
        matched_activities, matched_events = match_workouts(
            events,
            activities,
            self.config.workout_match_tss_threshold
        )

        # Phase 5: Build workout index
        logger.info("Building workout indices")
        workout_index = build_workout_index(matched_activities, matched_events)

        # Phase 6: Aggregate weekly summaries
        logger.info("Aggregating weekly summaries")
        weekly_stats = self._aggregate_weekly(matched_activities)

        # Phase 7: Save all data
        self._save_all_data(
            matched_activities,
            matched_events,
            power_curves,
            workout_index,
            weekly_stats
        )

        # Phase 8: Update metadata
        new_metadata = self._create_metadata(
            matched_activities,
            matched_events,
            len(activities) if do_full else len(new_activities),
            len(events)
        )
        save_sync_metadata(new_metadata, self.config)

        logger.info("=" * 60)
        logger.info("Athlete data sync complete")
        logger.info(f"Total activities: {len(matched_activities)}")
        logger.info(f"Total events: {len(matched_events)}")
        logger.info(f"Total weeks: {len(weekly_stats)}")
        logger.info("=" * 60)

        return {
            "success": True,
            "sync_type": "full" if do_full else "incremental",
            "total_activities": len(matched_activities),
            "new_activities": len(activities) if do_full else len(new_activities),
            "total_events": len(matched_events),
            "total_weeks": len(weekly_stats)
        }

    def _fetch_incremental_activities(self, since_date: str) -> list[dict]:
        """Fetch activities since last sync, always refreshing the last 2 weeks.

        This ensures any edits or updates to recent workouts on intervals.icu
        are reflected in the local data.

        Args:
            since_date: Date string in YYYY-MM-DD format

        Returns:
            List of activity dictionaries
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Always refresh the last 2 weeks to catch any edits/updates
        two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

        # Use the earlier of: 2 weeks ago or since_date
        oldest_date = min(two_weeks_ago, since_date) if since_date else two_weeks_ago

        logger.info(f"Fetching activities from {oldest_date} to {today} (refreshing last 2 weeks)")
        activities = self.intervals_client.get_workout_history(
            oldest_date=oldest_date,
            newest_date=today
        )

        logger.info(f"Fetched {len(activities)} activities")
        return activities

    def _fetch_full_activities(self) -> list[dict]:
        """Fetch 3 years of activity data.

        Returns:
            List of activity dictionaries
        """
        oldest_date = (datetime.now() - timedelta(days=self.config.history_initial_lookback_days)).strftime("%Y-%m-%d")
        newest_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Fetching activities from {oldest_date} to {newest_date}")
        activities = self.intervals_client.get_workout_history(
            oldest_date=oldest_date,
            newest_date=newest_date
        )

        logger.info(f"Fetched {len(activities)} activities")
        return activities

    def _fetch_planned_events(self, metadata: Optional[dict], force_full: bool) -> list[dict]:
        """Fetch planned workout events from intervals.icu.

        Always refreshes the last 2 weeks to catch any edits or updates.

        Args:
            metadata: Sync metadata for incremental fetching
            force_full: If True, fetch full range

        Returns:
            List of event dictionaries
        """
        last_event_date = get_last_event_date(metadata)
        two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

        if force_full or not last_event_date:
            # Full sync: 3 years back + 1 year forward
            oldest_date = (datetime.now() - timedelta(days=self.config.planned_events_lookback_days)).strftime("%Y-%m-%d")
            newest_date = (datetime.now() + timedelta(days=self.config.planned_events_lookahead_days)).strftime("%Y-%m-%d")
            logger.info(f"Fetching events (full): {oldest_date} to {newest_date}")
        else:
            # Incremental sync: always refresh last 2 weeks + future events
            oldest_date = min(two_weeks_ago, last_event_date) if last_event_date else two_weeks_ago
            newest_date = (datetime.now() + timedelta(days=self.config.planned_events_lookahead_days)).strftime("%Y-%m-%d")
            logger.info(f"Fetching events (incremental, refreshing last 2 weeks): {oldest_date} to {newest_date}")

        events = self.intervals_client.get_planned_events(
            oldest_date=oldest_date,
            newest_date=newest_date,
            category="WORKOUT"
        )

        logger.info(f"Fetched {len(events)} planned events")

        # Merge with existing events if incremental
        if not force_full and last_event_date:
            existing_events = self._load_existing_events()
            events = self._merge_events(existing_events, events)
            logger.info(f"Total events after merge: {len(events)}")

        return events

    def _load_existing_activities(self) -> list[dict]:
        """Load existing workout history from file.

        Returns:
            List of existing activity dictionaries
        """
        # Try new structure first
        history_path = self.config.athlete_data_dir / "raw" / "completed_activities.json"

        if not history_path.exists():
            # Fall back to old structure
            history_path = self.config.athlete_data_dir / "athlete_workout_history.json"

        if not history_path.exists():
            return []

        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Support both old and new format
                return data.get("workout_history", data.get("activities", []))
        except Exception as e:
            logger.error(f"Error loading existing activities: {e}")
            return []

    def _load_existing_events(self) -> list[dict]:
        """Load existing planned events from file.

        Returns:
            List of existing event dictionaries
        """
        events_path = self.config.athlete_data_dir / "raw" / "planned_events.json"

        if not events_path.exists():
            return []

        try:
            with open(events_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("events", [])
        except Exception as e:
            logger.error(f"Error loading existing events: {e}")
            return []

    def _merge_activities(self, existing: list[dict], new: list[dict]) -> list[dict]:
        """Deduplicate and merge activities by ID, keeping most recent.

        For incremental syncs, removes activities from the refreshed date range
        before adding new ones, ensuring deleted activities are removed.

        Args:
            existing: List of existing activities
            new: List of new activities

        Returns:
            Merged and deduplicated list
        """
        # Calculate the date range that was refreshed (last 2 weeks)
        two_weeks_ago = datetime.now() - timedelta(days=14)

        # Create dict with activity ID as key
        activities_dict = {}

        # Add existing activities, but exclude those in the refreshed date range
        for activity in existing:
            activity_id = activity.get("id")
            if not activity_id:
                continue

            # Parse activity date
            activity_date_str = activity.get("date", "")
            try:
                activity_date = datetime.fromisoformat(activity_date_str.split('T')[0])
                # Only keep activities older than 2 weeks (outside refresh window)
                if activity_date < two_weeks_ago:
                    activities_dict[activity_id] = activity
            except (ValueError, AttributeError):
                # If we can't parse the date, keep it to be safe
                activities_dict[activity_id] = activity

        # Add all new activities (includes everything from refreshed window)
        for activity in new:
            activity_id = activity.get("id")
            if activity_id:
                activities_dict[activity_id] = activity

        # Convert back to list and sort by date (newest first)
        merged = list(activities_dict.values())
        merged.sort(key=lambda x: x.get("date", ""), reverse=True)

        logger.info(f"Activity merge: {len(existing)} existing + {len(new)} new = {len(merged)} total")

        return merged

    def _merge_events(self, existing: list[dict], new: list[dict]) -> list[dict]:
        """Deduplicate and merge events by ID.

        For incremental syncs, removes events from the refreshed date range
        before adding new ones, ensuring deleted events are removed.

        Args:
            existing: List of existing events
            new: List of new events

        Returns:
            Merged and deduplicated list
        """
        # Calculate the date range that was refreshed (last 2 weeks)
        two_weeks_ago = datetime.now() - timedelta(days=14)

        # Create dict with event ID as key
        events_dict = {}

        # Add existing events, but exclude those in the refreshed date range
        for event in existing:
            event_id = event.get("id")
            if not event_id:
                continue

            # Parse event date
            event_date_str = event.get("start_date_local", "")
            try:
                event_date = datetime.fromisoformat(event_date_str.split('T')[0])
                # Only keep events older than 2 weeks (outside refresh window)
                if event_date < two_weeks_ago:
                    events_dict[event_id] = event
            except (ValueError, AttributeError):
                # If we can't parse the date, keep it to be safe
                events_dict[event_id] = event

        # Add all new events (includes everything from refreshed window)
        for event in new:
            event_id = event.get("id")
            if event_id:
                events_dict[event_id] = event

        # Convert back to list and sort by date
        merged = list(events_dict.values())
        merged.sort(key=lambda x: x.get("start_date_local", ""), reverse=True)

        logger.info(f"Event merge: {len(existing)} existing + {len(new)} new = {len(merged)} total")

        return merged

    def _aggregate_weekly(self, activities: list[dict]) -> dict:
        """Compute weekly summaries from activities.

        Args:
            activities: List of activity dictionaries

        Returns:
            Dict mapping week start dates to aggregated stats
        """
        weekly_data = defaultdict(lambda: {
            "total_time_seconds": 0,
            "total_distance_km": 0.0,
            "total_elevation_gain_m": 0.0,
            "total_tss": 0.0,
            "total_time_in_zones": {
                "zone_1": 0,
                "zone_2": 0,
                "zone_3": 0,
                "zone_4": 0,
                "zone_5": 0
            },
            "workout_count": 0
        })

        for activity in activities:
            # Parse activity date
            date_str = activity.get("date")
            if not date_str:
                continue

            try:
                activity_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse date: {date_str}")
                continue

            # Calculate week start (Monday)
            week_start = activity_date - timedelta(days=activity_date.weekday())
            week_key = week_start.strftime("%Y-%m-%d")

            # Aggregate metrics
            weekly_data[week_key]["total_time_seconds"] += activity.get("duration_seconds") or 0
            weekly_data[week_key]["total_distance_km"] += (activity.get("distance_meters") or 0) / 1000
            weekly_data[week_key]["total_tss"] += activity.get("training_stress_score") or 0.0
            weekly_data[week_key]["workout_count"] += 1

            # Aggregate time in zones
            time_in_zones = activity.get("power_zone_times", [])
            if time_in_zones and isinstance(time_in_zones, list):
                for zone in time_in_zones:
                    zone_id = zone.get("id")
                    zone_secs = zone.get("secs", 0)

                    zone_mapping = {
                        "Z1": "zone_1",
                        "Z2": "zone_2",
                        "Z3": "zone_3",
                        "Z4": "zone_4",
                        "Z5": "zone_5"
                    }

                    if zone_id in zone_mapping:
                        weekly_data[week_key]["total_time_in_zones"][zone_mapping[zone_id]] += zone_secs

        # Convert defaultdict to regular dict and add computed fields
        result = {}
        for week_key in sorted(weekly_data.keys(), reverse=True):
            stats = weekly_data[week_key]

            result[week_key] = {
                "week_start": week_key,
                "total_time_seconds": stats["total_time_seconds"],
                "total_time_hours": round(stats["total_time_seconds"] / 3600, 2),
                "total_distance_km": round(stats["total_distance_km"], 2),
                "total_tss": round(stats["total_tss"], 1),
                "total_time_in_zones": stats["total_time_in_zones"],
                "workout_count": stats["workout_count"]
            }

        return result

    def _load_existing_power_curves(self) -> dict:
        """Load existing power curves from file.

        Returns:
            Power curve dictionary or empty dict if not found
        """
        power_path = self.config.athlete_data_dir / "raw" / "power_curves.json"

        if not power_path.exists():
            return {}

        try:
            with open(power_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("max_power", {})
        except Exception as e:
            logger.error(f"Error loading existing power curves: {e}")
            return {}

    def _fetch_power_curves(self) -> dict:
        """Fetch fresh power curve data.

        Returns:
            Power curve dictionary
        """
        power_curves = self.intervals_client.get_power_curves()

        # Transform to match expected format
        period_mapping = {
            "1_month": "30_day",
            "3_months": "90_day",
            "6_months": "180_day",
            "12_months": "all_time"
        }

        result = {}
        for old_key, new_key in period_mapping.items():
            if old_key in power_curves:
                result[new_key] = power_curves[old_key]

        return result

    def _save_all_data(
        self,
        activities: list[dict],
        events: list[dict],
        power_curves: dict,
        workout_index: dict,
        weekly_stats: dict
    ):
        """Save all data to JSON files in new structure.

        Args:
            activities: List of activities
            events: List of events
            power_curves: Power curve data
            workout_index: Workout index data
            weekly_stats: Weekly summary data
        """
        # Ensure directories exist
        raw_dir = self.config.athlete_data_dir / "raw"
        processed_dir = self.config.athlete_data_dir / "processed"
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Save completed activities
        activities_path = raw_dir / "completed_activities.json"
        with open(activities_path, 'w', encoding='utf-8') as f:
            json.dump({
                "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "total_count": len(activities),
                "activities": activities
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(activities)} activities to {activities_path}")

        # Save planned events
        events_path = raw_dir / "planned_events.json"
        with open(events_path, 'w', encoding='utf-8') as f:
            json.dump({
                "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "total_count": len(events),
                "events": events
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(events)} events to {events_path}")

        # Save power curves
        power_path = raw_dir / "power_curves.json"
        with open(power_path, 'w', encoding='utf-8') as f:
            json.dump({"max_power": power_curves}, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved power curves to {power_path}")

        # Save workout index
        index_path = processed_dir / "workout_index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(workout_index, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved workout index to {index_path}")

        # Save weekly summary
        weekly_path = processed_dir / "weekly_summary.json"
        with open(weekly_path, 'w', encoding='utf-8') as f:
            json.dump({"weekly_summary": weekly_stats}, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(weekly_stats)} weeks to {weekly_path}")

    def _create_metadata(
        self,
        activities: list[dict],
        events: list[dict],
        new_activity_count: int,
        new_event_count: int
    ) -> dict:
        """Create sync metadata from activities and events.

        Args:
            activities: List of all activities
            events: List of all events
            new_activity_count: Number of new activities fetched
            new_event_count: Number of new events fetched

        Returns:
            Metadata dictionary
        """
        # Find the most recent activity date
        last_activity_date = None
        last_activity_id = None

        if activities:
            # Activities are already sorted newest first
            most_recent = activities[0]
            last_activity_date = most_recent.get("date")
            last_activity_id = most_recent.get("id")

        # Find the most recent event date
        last_event_date = None
        last_event_id = None

        if events:
            # Events are sorted by start_date_local
            most_recent = events[0]
            last_event_date = most_recent.get("start_date_local", "").split('T')[0]
            last_event_id = most_recent.get("id")

        return {
            "schema_version": "2.0",
            "last_sync_timestamp": datetime.now().isoformat(),
            "last_activity_date": last_activity_date,
            "last_activity_id": last_activity_id,
            "total_activities": len(activities),
            "last_event_date": last_event_date,
            "last_event_id": last_event_id,
            "total_events": len(events),
            "sync_history": [{
                "timestamp": datetime.now().isoformat(),
                "type": "sync",
                "new_activities": new_activity_count,
                "new_events": new_event_count,
                "success": True
            }]
        }
