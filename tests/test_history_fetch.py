"""Test script for intervals.icu history fetching functionality."""
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path

from src.config import AppConfig
from src.integrations.intervals import IntervalsClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test-history')

def test_get_user_workout_history():
    """Test fetching workout history from intervals.icu."""

    # Load config
    config = AppConfig.from_env()
    logger.info("Configuration loaded")

    # Initialize client
    intervals_client = IntervalsClient(
        api_key=config.intervals_api_key,
        athlete_id=config.default_athlete_id
    )
    logger.info(f"IntervalsClient initialized for athlete: {intervals_client.athlete_id}")

    # Test 1: Connection test
    logger.info("\n=== Test 1: Connection Test ===")
    if intervals_client.test_connection():
        logger.info("✓ Connection successful")
    else:
        logger.error("✗ Connection failed")
        return

    # Test 2: Fetch last 30 days of history with transformed fields
    logger.info("\n=== Test 2: Fetch Last 30 Days (Transformed Fields) ===")
    oldest_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    newest_date = datetime.now().strftime("%Y-%m-%d")

    try:
        history = intervals_client.get_workout_history(
            oldest_date=oldest_date,
            newest_date=newest_date
        )
        logger.info(f"✓ Fetched {len(history)} workouts with transformed fields")

        if history:
            # Show sample activity with new field names
            sample = history[0]
            logger.info(f"\nSample transformed activity:")
            for key, value in sample.items():
                logger.info(f"  {key}: {value}")

            logger.info(f"\nAll transformed fields in sample:")
            logger.info(f"  {', '.join(sample.keys())}")

            # Verify expected transformed fields are present
            logger.info(f"\nVerifying transformed field names:")
            expected_fields = [
                'date', 'type', 'duration_seconds', 'distance_meters',
                'avg_power_watts', 'normalized_power_watts', 'intensity_factor',
                'training_stress_score', 'power_zone_times',
                'acute_training_load', 'chronic_training_load'
            ]
            for field in expected_fields:
                value = sample.get(field)
                status = "✓" if field in sample else "✗"
                logger.info(f"  {status} {field}: {value}")

    except Exception as e:
        logger.error(f"✗ Error fetching history: {str(e)}", exc_info=True)
        return

    # Test 3: Fetch last 12 months automatically (default behavior)
    logger.info("\n=== Test 3: Fetch Last 12 Months (Automatic) ===")
    try:
        history_12m = intervals_client.get_workout_history()
        logger.info(f"✓ Fetched {len(history_12m)} workouts from last 12 months automatically")

    except Exception as e:
        logger.error(f"✗ Error fetching 12-month history: {str(e)}", exc_info=True)
        return

    # Test 4: Fetch power curves
    logger.info("\n=== Test 4: Fetch Power Curves ===")
    try:
        power_curves = intervals_client.get_power_curves()
        logger.info(f"✓ Fetched power curves for {len(power_curves)} time periods")

        # Display power curves for each time period
        for period, curves in power_curves.items():
            logger.info(f"\n{period.replace('_', ' ').title()}:")
            if isinstance(curves, dict) and 'error' not in curves:
                # Show first few durations
                for i, (duration, watts) in enumerate(list(curves.items())[:6]):
                    logger.info(f"  {duration.replace('_', ' ')}: {watts}W")
                if len(curves) > 6:
                    logger.info(f"  ... and {len(curves) - 6} more durations")
            else:
                logger.warning(f"  No data or error: {curves}")

    except Exception as e:
        logger.error(f"✗ Error fetching power curves: {str(e)}", exc_info=True)
        # Continue with remaining tests even if power curves fail
        logger.info("  Note: Power curves endpoint may not be available or configured")

    # Test 5: Save history to file
    logger.info("\n=== Test 5: Save History to File ===")
    try:
        history_dir = config.data_dir / "workout_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_history_{timestamp}.json"
        filepath = history_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Saved to: {filepath}")
        logger.info(f"  File size: {filepath.stat().st_size} bytes")

    except Exception as e:
        logger.error(f"✗ Error saving history: {str(e)}", exc_info=True)
        return

    logger.info("\n=== All Tests Completed ===")

if __name__ == "__main__":
    test_get_user_workout_history()
