"""Get history tool implementation."""
import logging
import json
from datetime import datetime
from typing import TYPE_CHECKING

from src.config import AppConfig
from src.integrations.intervals import IntervalsClient

# Import for type hints only to avoid circular dependency
if TYPE_CHECKING:
    from src.services.coach_service import CoachService


def execute(
    args: dict,
    config: AppConfig,
    coach_service: "CoachService" = None
) -> dict:
    """Execute get_user_workout_history tool.

    Args:
        args: Tool arguments (oldest_date, newest_date - both optional)
        config: Application configuration with API keys and paths
        coach_service: CoachService instance (not used for this tool)

    Returns:
        Result dict with confirmation message
    """
    logger = logging.getLogger('train-r')

    try:
        # Extract optional parameters
        oldest_date = args.get("oldest_date")
        newest_date = args.get("newest_date")

        logger.info(f"Fetching workout history (oldest={oldest_date}, newest={newest_date})")

        # Initialize intervals.icu client
        intervals_client = IntervalsClient(api_key=config.intervals_api_key, config=config)

        # Fetch workout history
        history = intervals_client.get_workout_history(
            oldest_date=oldest_date,
            newest_date=newest_date
        )

        logger.info(f"Retrieved {len(history)} workouts from intervals.icu")

        # Ensure history directory exists
        history_dir = config.data_dir / "workout_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        # Save history to JSON file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"history_{timestamp}.json"
        filepath = history_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        logger.info(f"Workout history saved to: {filepath}")

        # Return simple confirmation (data manipulation comes later)
        return {
            "success": True,
            "message": "history fetched",
            "workout_count": len(history),
            "saved_to": str(filepath)
        }

    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch history: {str(e)}"
        }
