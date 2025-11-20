"""Standalone script to upload workouts to intervals.icu."""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.integrations.intervals import IntervalsClient
from src.config import AppConfig, UPLOAD_DEFAULT_HOUR, UPLOAD_DEFAULT_MINUTE

# Get project root (parent of src directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent


def list_workouts(workout_dir: str) -> list[Path]:
    """List all .zwo files in the workout directory.

    Args:
        workout_dir: Directory containing workout files

    Returns:
        List of workout file paths
    """
    workout_path = Path(workout_dir)
    if not workout_path.exists():
        return []

    workouts = sorted(workout_path.glob("*.zwo"), reverse=True)
    return workouts


def display_workout_menu(workouts: list[Path]) -> None:
    """Display workout selection menu.

    Args:
        workouts: List of workout file paths
    """
    print("\nAvailable workouts:")
    print("-" * 60)
    for idx, workout in enumerate(workouts, 1):
        print(f"{idx}. {workout.name}")
    print("-" * 60)


def get_workout_selection(workouts: list[Path]) -> Path:
    """Get workout selection from user.

    Args:
        workouts: List of workout file paths

    Returns:
        Selected workout path

    Raises:
        SystemExit: If user cancels or invalid selection
    """
    while True:
        try:
            selection = input("\nSelect workout number (or 'q' to quit): ").strip()

            if selection.lower() == 'q':
                print("Cancelled.")
                sys.exit(0)

            idx = int(selection)
            if 1 <= idx <= len(workouts):
                return workouts[idx - 1]
            else:
                print(f"Please enter a number between 1 and {len(workouts)}")

        except ValueError:
            print("Please enter a valid number")


def get_target_date() -> str:
    """Get target date/time for workout from user.

    Returns:
        ISO formatted date string (YYYY-MM-DDTHH:MM:SS)
    """
    print("\nWhen should this workout be scheduled?")
    print("1. Today")
    print("2. Tomorrow")
    print("3. Custom date")

    while True:
        choice = input("\nSelect option (1-3): ").strip()

        if choice == "1":
            date = datetime.now()
            break
        elif choice == "2":
            date = datetime.now() + timedelta(days=1)
            break
        elif choice == "3":
            date_str = input("Enter date (YYYY-MM-DD): ").strip()
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                break
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD")
                continue
        else:
            print("Please enter 1, 2, or 3")

    # Get time
    time_str = input(f"Enter time (HH:MM, default {UPLOAD_DEFAULT_HOUR:02d}:{UPLOAD_DEFAULT_MINUTE:02d}): ").strip()
    if not time_str:
        time_str = f"{UPLOAD_DEFAULT_HOUR:02d}:{UPLOAD_DEFAULT_MINUTE:02d}"

    try:
        time_parts = time_str.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        date = date.replace(hour=hour, minute=minute, second=0)
    except (ValueError, IndexError):
        print(f"Invalid time format, using {UPLOAD_DEFAULT_HOUR:02d}:{UPLOAD_DEFAULT_MINUTE:02d}")
        date = date.replace(hour=UPLOAD_DEFAULT_HOUR, minute=UPLOAD_DEFAULT_MINUTE, second=0)

    return date.strftime("%Y-%m-%dT%H:%M:%S")


def main():
    """Main script execution."""
    load_dotenv()

    print("=== intervals.icu Workout Uploader ===\n")

    # Load config
    try:
        config = AppConfig.from_env()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # Initialize uploader
    try:
        intervals_client = IntervalsClient(api_key=config.intervals_api_key, config=config)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Test connection
    print("Testing connection to intervals.icu...")
    if not intervals_client.test_connection():
        print("Error: Could not connect to intervals.icu")
        print("Please check your API key and internet connection")
        sys.exit(1)
    print("Connection successful!\n")

    # List workouts
    workout_dir = str(PROJECT_ROOT / "data/created_workouts")
    workouts = list_workouts(workout_dir)

    if not workouts:
        print(f"No workouts found in {workout_dir}")
        sys.exit(0)

    # Display menu and get selection
    display_workout_menu(workouts)
    selected_workout = get_workout_selection(workouts)

    print(f"\nSelected: {selected_workout.name}")

    # Get target date
    target_date = get_target_date()

    # Confirm upload
    print(f"\nReady to upload:")
    print(f"  File: {selected_workout.name}")
    print(f"  Date: {target_date}")

    confirm = input("\nProceed with upload? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Upload cancelled.")
        sys.exit(0)

    # Upload workout
    print("\nUploading workout...")
    try:
        response = intervals_client.upload_workout(
            file_path=str(selected_workout),
            start_date=target_date,
            external_id=f"train-r-{selected_workout.stem}"
        )

        print("\nUpload successful!")
        print(f"Event ID: {response.get('id', 'N/A')}")
        print(f"Name: {response.get('name', 'N/A')}")

    except Exception as e:
        print(f"\nUpload failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
