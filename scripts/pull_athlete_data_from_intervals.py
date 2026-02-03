"""Pull athlete data from intervals.icu API.

This script fetches athlete workout history and power data from intervals.icu
and stores it for the Train-R dashboard and AI coach.

Usage:
    # Default: fetch last 12 months of workouts
    uv run python scripts/pull_athlete_data_from_intervals.py

    # Fetch only last 10 workouts
    uv run python scripts/pull_athlete_data_from_intervals.py --limit 10

    # Custom date range
    uv run python scripts/pull_athlete_data_from_intervals.py --oldest 2025-01-01 --newest 2025-10-31
"""
import argparse
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from src.config import AppConfig
from src.integrations.intervals import IntervalsClient

# Initialize logger
logger = logging.getLogger('train-r')


def transform_zone_times(zone_array: Optional[list[dict]]) -> dict:
    """Transform zone times from array to flat dictionary format.

    Args:
        zone_array: Array of zone objects like [{"id": "Z1", "secs": 1016}, ...]

    Returns:
        Dict mapping zone names to seconds, e.g. {"zone_1": 1016, "zone_2": 2585, ...}
    """
    if not zone_array:
        return {
            "zone_1": None,
            "zone_2": None,
            "zone_3": None,
            "zone_4": None,
            "zone_5": None
        }

    zone_mapping = {
        "Z1": "zone_1",
        "Z2": "zone_2",
        "Z3": "zone_3",
        "Z4": "zone_4",
        "Z5": "zone_5"
    }

    result = {}
    for zone in zone_array:
        zone_id = zone.get("id")
        if zone_id in zone_mapping:
            result[zone_mapping[zone_id]] = zone.get("secs")

    # Ensure all zones present
    for zone_key in zone_mapping.values():
        if zone_key not in result:
            result[zone_key] = None

    return result


def map_power_curve_periods(power_curves: dict) -> dict:
    """Transform power curve period names to match template format.

    Args:
        power_curves: Dict with keys like "1_month", "2_months", etc.

    Returns:
        Dict with keys like "30_day", "90_day", "180_day", "all_time"
    """
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


def enrich_workout_data(
    workout: dict,
    intervals_client: IntervalsClient
) -> dict:
    """Enrich workout with additional data from intervals.icu.

    Args:
        workout: Base workout dict from get_workout_history
        intervals_client: IntervalsClient instance

    Returns:
        Enriched workout dict matching template format
    """
    # Extract activity ID from the workout data
    activity_id = workout.get("id")

    if not activity_id:
        logger.warning("Workout missing activity ID, skipping enrichment")
        return transform_to_template_format(workout, None)

    # Skip enrichment for external activities (e.g., synced from Strava)
    # Only internal intervals.icu activities (with "i" prefix) support detail fetching
    activity_id_str = str(activity_id)
    if not activity_id_str.startswith("i"):
        logger.info(f"Skipping enrichment for external activity {activity_id}")
        return transform_to_template_format(workout, None)

    try:
        # Longer delay to avoid rate limiting (0.5s between requests)
        time.sleep(0.5)

        # Fetch activity details for name and elevation
        # Note: activity ID must include the prefix (e.g., "i118382427")
        activity_details = intervals_client.get_activity_details(activity_id_str)

        return transform_to_template_format(workout, activity_details)

    except Exception as e:
        # Log warning for timeouts/errors and continue with basic data
        logger.warning(f"Could not enrich workout {activity_id}, using basic data: {str(e)[:100]}")
        # Return basic transformed data on error
        return transform_to_template_format(workout, None)


def transform_to_template_format(
    workout: dict,
    activity_details: Optional[dict]
) -> dict:
    """Transform workout data to match template format.

    Args:
        workout: Base workout data
        activity_details: Full activity details (may be None)

    Returns:
        Workout dict matching template format
    """
    distance_meters = workout.get("distance_meters")
    distance_km = None
    if distance_meters is not None:
        try:
            distance_km = distance_meters / 1000
        except Exception:
            distance_km = None

    return {
        "date": workout.get("date"),
        "duration": workout.get("duration_seconds"),
        "name": activity_details.get("name") if activity_details else None,
        "tss": workout.get("training_stress_score"),
        "np": workout.get("normalized_power_watts"),
        "avg_power": workout.get("avg_power_watts"),
        "if": workout.get("intensity_factor"),
        "distance_km": distance_km,
        "elevation_gain_m": activity_details.get("total_elevation_gain") if activity_details else None,
        "time_in_zones": transform_zone_times(workout.get("power_zone_times"))
    }


def aggregate_weekly_stats(workouts: list[dict]) -> dict:
    """Aggregate workout data into weekly summaries.

    Args:
        workouts: List of workout dicts with date, duration, tss, etc.

    Returns:
        Dict mapping week start dates (ISO format) to aggregated stats
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

    for workout in workouts:
        # Parse workout date
        date_str = workout.get("date")
        if not date_str:
            continue

        try:
            workout_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse date: {date_str}")
            continue

        # Calculate week start (Monday)
        week_start = workout_date - timedelta(days=workout_date.weekday())
        week_key = week_start.strftime("%Y-%m-%d")

        # Aggregate metrics
        weekly_data[week_key]["total_time_seconds"] += workout.get("duration") or 0
        weekly_data[week_key]["total_distance_km"] += workout.get("distance_km") or 0.0
        weekly_data[week_key]["total_elevation_gain_m"] += workout.get("elevation_gain_m") or 0.0
        weekly_data[week_key]["total_tss"] += workout.get("tss") or 0.0
        weekly_data[week_key]["workout_count"] += 1

        # Aggregate time in zones
        time_in_zones = workout.get("time_in_zones", {})
        for zone in ["zone_1", "zone_2", "zone_3", "zone_4", "zone_5"]:
            zone_time = time_in_zones.get(zone)
            if zone_time:
                weekly_data[week_key]["total_time_in_zones"][zone] += zone_time

    # Convert defaultdict to regular dict and sort by week
    result = {}
    for week_key in sorted(weekly_data.keys(), reverse=True):
        stats = weekly_data[week_key]

        # Round numeric values for cleaner output
        result[week_key] = {
            "week_start": week_key,
            "total_time_seconds": stats["total_time_seconds"],
            "total_time_hours": round(stats["total_time_seconds"] / 3600, 2),
            "total_distance_km": round(stats["total_distance_km"], 2),
            "total_elevation_gain_m": round(stats["total_elevation_gain_m"], 1),
            "total_tss": round(stats["total_tss"], 1),
            "total_time_in_zones": stats["total_time_in_zones"],
            "workout_count": stats["workout_count"]
        }

    return result


def generate_test_data(
    oldest_date: Optional[str] = None,
    newest_date: Optional[str] = None,
    limit: Optional[int] = None,
    skip_enrichment: bool = False
):
    """Generate structured test data from intervals.icu.

    Args:
        oldest_date: Start date in YYYY-MM-DD format (optional)
        newest_date: End date in YYYY-MM-DD format (optional)
        limit: Maximum number of workouts to fetch (optional)
        skip_enrichment: Skip fetching additional activity details (faster but less data)
    """
    # Load configuration
    config = AppConfig.from_env()
    config.create_directories()

    logger.info("=" * 60)
    logger.info("Starting test data generation")
    logger.info("=" * 60)

    # Initialize intervals.icu client
    intervals_client = IntervalsClient(
        api_key=config.intervals_api_key,
        config=config
    )

    # Check for existing data and determine date range
    workout_history_path = config.athlete_data_dir / "athlete_workout_history.json"
    existing_workouts = []

    if workout_history_path.exists() and not oldest_date:
        try:
            with open(workout_history_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_workouts = existing_data.get("workout_history", [])

            if existing_workouts:
                # Find most recent workout date
                dates = [w.get("date") for w in existing_workouts if w.get("date")]
                if dates:
                    most_recent = max(dates)
                    # Parse and add one day to avoid duplicates
                    most_recent_dt = datetime.fromisoformat(most_recent.replace('Z', '+00:00'))
                    oldest_date = (most_recent_dt + timedelta(days=1)).strftime("%Y-%m-%d")
                    logger.info(f"Found existing data, fetching workouts newer than {oldest_date}")
        except Exception as e:
            logger.warning(f"Could not load existing workout history: {e}")

    # Fetch base workout history
    logger.info(f"Fetching workout history (oldest={oldest_date}, newest={newest_date})")
    history = intervals_client.get_workout_history(
        oldest_date=oldest_date,
        newest_date=newest_date
    )

    logger.info(f"Retrieved {len(history)} workouts from intervals.icu")

    # Apply limit if specified
    if limit and limit < len(history):
        logger.info(f"Limiting to most recent {limit} workouts")
        history = history[:limit]

    # Enrich each workout with additional data
    enriched_workouts = []
    total = len(history)

    if skip_enrichment:
        logger.info("Skipping enrichment - using basic workout data only")
        for workout in history:
            enriched_workouts.append(transform_to_template_format(workout, None))
    else:
        for idx, workout in enumerate(history, 1):
            logger.info(f"Processing workout {idx}/{total}...")
            enriched = enrich_workout_data(workout, intervals_client)
            enriched_workouts.append(enriched)

    # Fetch aggregate power curves
    logger.info("Fetching aggregate power curves...")
    power_curves = intervals_client.get_power_curves()

    # Transform power curve periods to match template
    transformed_power_curves = map_power_curve_periods(power_curves)

    # Merge with existing workouts if any
    if existing_workouts:
        logger.info(f"Merging {len(enriched_workouts)} new workouts with {len(existing_workouts)} existing workouts")
        all_workouts = existing_workouts + enriched_workouts
    else:
        all_workouts = enriched_workouts

    # Generate weekly aggregated statistics from all workouts
    logger.info("Aggregating weekly statistics...")
    weekly_stats = aggregate_weekly_stats(all_workouts)
    weeks_count = len(weekly_stats)
    logger.info(f"Generated statistics for {weeks_count} weeks")

    # Prepare final data structures
    workout_history_data = {
        "workout_history": all_workouts
    }

    power_history_data = {
        "max_power": transformed_power_curves
    }

    weekly_summary_data = {
        "weekly_summary": weekly_stats
    }

    # Save to athlete data directory
    workout_history_path = config.athlete_data_dir / "athlete_workout_history.json"
    power_history_path = config.athlete_data_dir / "athlete_power_history.json"
    weekly_summary_path = config.athlete_data_dir / "athlete_weekly_summary.json"

    logger.info(f"Saving workout history to {workout_history_path}")
    with open(workout_history_path, 'w', encoding='utf-8') as f:
        json.dump(workout_history_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saving power history to {power_history_path}")
    with open(power_history_path, 'w', encoding='utf-8') as f:
        json.dump(power_history_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saving weekly summary to {weekly_summary_path}")
    with open(weekly_summary_path, 'w', encoding='utf-8') as f:
        json.dump(weekly_summary_data, f, indent=2, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info("Test data generation complete!")
    logger.info(f"New workouts: {len(enriched_workouts)}")
    logger.info(f"Total workouts: {len(all_workouts)}")
    logger.info(f"Weeks summarized: {weeks_count}")
    logger.info(f"Workout history: {workout_history_path}")
    logger.info(f"Power history: {power_history_path}")
    logger.info(f"Weekly summary: {weekly_summary_path}")
    logger.info("=" * 60)


def main():
    """Main entry point for script."""
    parser = argparse.ArgumentParser(
        description="Generate structured test data from intervals.icu API"
    )
    parser.add_argument(
        "--oldest",
        type=str,
        help="Start date in YYYY-MM-DD format (default: 12 months ago)"
    )
    parser.add_argument(
        "--newest",
        type=str,
        help="End date in YYYY-MM-DD format (default: today)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of workouts to fetch (default: all)"
    )
    parser.add_argument(
        "--skip-enrichment",
        action="store_true",
        help="Skip fetching activity details for faster processing (no names/elevation data)"
    )

    args = parser.parse_args()

    try:
        generate_test_data(
            oldest_date=args.oldest,
            newest_date=args.newest,
            limit=args.limit,
            skip_enrichment=args.skip_enrichment
        )
    except Exception as e:
        logger.error(f"Test data generation failed: {str(e)}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
