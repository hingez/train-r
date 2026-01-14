"""Data migration service for upgrading JSON file structure."""
import json
import logging
import shutil
from pathlib import Path
from src.config import AppConfig

logger = logging.getLogger('train-r')


def migrate_to_v2(config: AppConfig) -> bool:
    """Migrate from flat structure to raw/processed structure.

    Old structure:
        data/athlete/
        ├── athlete_workout_history.json
        ├── athlete_power_history.json
        ├── athlete_weekly_summary.json
        └── sync_metadata.json

    New structure:
        data/athlete/
        ├── raw/
        │   ├── completed_activities.json
        │   ├── planned_events.json
        │   └── power_curves.json
        ├── processed/
        │   ├── workout_index.json
        │   └── weekly_summary.json
        └── sync_metadata.json

    Args:
        config: Application configuration

    Returns:
        True if migration performed, False if already migrated
    """
    raw_dir = config.athlete_data_dir / "raw"
    processed_dir = config.athlete_data_dir / "processed"

    # Check if already migrated
    if raw_dir.exists() and processed_dir.exists():
        logger.info("Data already migrated to v2 structure")
        return False

    logger.info("=" * 60)
    logger.info("Migrating data structure to v2")
    logger.info("=" * 60)

    # Create new directories
    raw_dir.mkdir(exist_ok=True)
    processed_dir.mkdir(exist_ok=True)
    logger.info(f"Created directories: raw/ and processed/")

    # Migrate workout history
    old_history = config.athlete_data_dir / "athlete_workout_history.json"
    new_history = raw_dir / "completed_activities.json"

    if old_history.exists():
        shutil.copy2(old_history, new_history)
        logger.info(f"Migrated: athlete_workout_history.json -> raw/completed_activities.json")
    else:
        logger.info("No existing workout history to migrate")

    # Migrate power curves
    old_power = config.athlete_data_dir / "athlete_power_history.json"
    new_power = raw_dir / "power_curves.json"

    if old_power.exists():
        shutil.copy2(old_power, new_power)
        logger.info(f"Migrated: athlete_power_history.json -> raw/power_curves.json")
    else:
        logger.info("No existing power curves to migrate")

    # Migrate weekly summary
    old_weekly = config.athlete_data_dir / "athlete_weekly_summary.json"
    new_weekly = processed_dir / "weekly_summary.json"

    if old_weekly.exists():
        shutil.copy2(old_weekly, new_weekly)
        logger.info(f"Migrated: athlete_weekly_summary.json -> processed/weekly_summary.json")
    else:
        logger.info("No existing weekly summary to migrate")

    # Update metadata schema version
    metadata_path = config.athlete_data_dir / "sync_metadata.json"

    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            metadata["schema_version"] = "2.0"

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info("Updated metadata schema version to 2.0")
        except Exception as e:
            logger.error(f"Error updating metadata: {e}")
    else:
        logger.info("No existing metadata to update")

    logger.info("=" * 60)
    logger.info("Migration to v2 complete")
    logger.info("=" * 60)

    return True
