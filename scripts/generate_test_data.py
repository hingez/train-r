"""Generate structured test data from intervals.icu API.

This script fetches athlete workout history and power data from intervals.icu
and populates the template files with real data for testing purposes.

Usage:
    # Default: fetch last 12 months of workouts
    uv run python scripts/generate_test_data.py

    # Fetch only last 10 workouts (faster for testing)
    uv run python scripts/generate_test_data.py --limit 10

    # Custom date range
    uv run python scripts/generate_test_data.py --oldest 2025-01-01 --newest 2025-10-31
"""
import argparse
import json
import logging
import time
from datetime import datetime
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

    try:
        # Small delay to avoid rate limiting
        time.sleep(0.1)

        # Fetch activity details for name and elevation
        activity_details = intervals_client.get_activity_details(str(activity_id))

        return transform_to_template_format(workout, activity_details)

    except Exception as e:
        logger.error(f"Error enriching workout {activity_id}: {str(e)}")
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
    return {
        "date": workout.get("date"),
        "duration": workout.get("duration_seconds"),
        "name": activity_details.get("name") if activity_details else None,
        "tss": workout.get("training_stress_score"),
        "np": workout.get("normalized_power_watts"),
        "avg_power": workout.get("avg_power_watts"),
        "if": workout.get("intensity_factor"),
        "distance_km": workout.get("distance_meters") / 1000,
        "elevation_gain_m": activity_details.get("total_elevation_gain") if activity_details else None,
        "time_in_zones": transform_zone_times(workout.get("power_zone_times"))
    }


def generate_test_data(
    oldest_date: Optional[str] = None,
    newest_date: Optional[str] = None,
    limit: Optional[int] = None
):
    """Generate structured test data from intervals.icu.

    Args:
        oldest_date: Start date in YYYY-MM-DD format (optional)
        newest_date: End date in YYYY-MM-DD format (optional)
        limit: Maximum number of workouts to fetch (optional)
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

    for idx, workout in enumerate(history, 1):
        logger.info(f"Processing workout {idx}/{total}...")
        enriched = enrich_workout_data(workout, intervals_client)
        enriched_workouts.append(enriched)

    # Fetch aggregate power curves
    logger.info("Fetching aggregate power curves...")
    power_curves = intervals_client.get_power_curves()

    # Transform power curve periods to match template
    transformed_power_curves = map_power_curve_periods(power_curves)

    # Prepare final data structures
    workout_history_data = {
        "workout_history": enriched_workouts
    }

    power_history_data = {
        "max_power": transformed_power_curves
    }

    # Save to template file locations
    workout_history_path = config.athlete_data_dir / "athelete_workout_history.json"
    power_history_path = config.athlete_data_dir / "athelete_power_history.json"

    logger.info(f"Saving workout history to {workout_history_path}")
    with open(workout_history_path, 'w', encoding='utf-8') as f:
        json.dump(workout_history_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saving power history to {power_history_path}")
    with open(power_history_path, 'w', encoding='utf-8') as f:
        json.dump(power_history_data, f, indent=2, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info("Test data generation complete!")
    logger.info(f"Workouts processed: {len(enriched_workouts)}")
    logger.info(f"Workout history: {workout_history_path}")
    logger.info(f"Power history: {power_history_path}")
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

    args = parser.parse_args()

    try:
        generate_test_data(
            oldest_date=args.oldest,
            newest_date=args.newest,
            limit=args.limit
        )
    except Exception as e:
        logger.error(f"Test data generation failed: {str(e)}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
