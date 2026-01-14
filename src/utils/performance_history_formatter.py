"""Format athlete performance history for LLM context.

Loads workout data and formats it into a readable summary for the system prompt.
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger('train-r')


def format_performance_history(data_dir: Path) -> str:
    """Load and format last 4 weeks of workout data + next 4 weeks of planned workouts for LLM context.

    Args:
        data_dir: Path to athlete data directory

    Returns:
        JSON-formatted performance history string
    """
    try:
        # Load JSON files
        workout_index_path = data_dir / "processed" / "workout_index.json"
        weekly_summary_path = data_dir / "processed" / "weekly_summary.json"
        activities_path = data_dir / "raw" / "completed_activities.json"
        planned_events_path = data_dir / "raw" / "planned_events.json"

        if not workout_index_path.exists() or not weekly_summary_path.exists():
            return json.dumps({"error": "No performance history available. Run data sync to populate workout history."})

        with open(workout_index_path) as f:
            workout_index = json.load(f)
        with open(weekly_summary_path) as f:
            weekly_summary = json.load(f)
        with open(activities_path) as f:
            activities_data = json.load(f)

        # Load planned events if available
        planned_events = []
        if planned_events_path.exists():
            with open(planned_events_path) as f:
                planned_data = json.load(f)
                planned_events = planned_data.get("events", [])

        # Filter last 28 days for history
        cutoff_date_past = datetime.now() - timedelta(days=28)
        start_date_past = cutoff_date_past.strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        # Next 28 days for future workouts
        cutoff_date_future = datetime.now() + timedelta(days=28)
        end_date_future = cutoff_date_future.strftime("%Y-%m-%d")

        # Build JSON structure
        performance_data = {
            "past_period": f"{start_date_past} to {end_date}",
            "future_period": f"{end_date} to {end_date_future}",
            "past_weeks": _format_weekly_overview(weekly_summary, activities_data, cutoff_date_past),
            "past_workouts": _format_workout_log(workout_index, cutoff_date_past),
            "future_workouts": _format_future_workouts(planned_events),
            "summary": _calculate_summary_statistics(workout_index, cutoff_date_past)
        }

        # Return compact JSON (no indentation for token efficiency)
        return json.dumps(performance_data, separators=(',', ':'))

    except FileNotFoundError as e:
        logger.warning(f"Performance history file not found: {e}")
        return json.dumps({"error": "No performance history available."})
    except Exception as e:
        logger.error(f"Error formatting performance history: {e}", exc_info=True)
        return json.dumps({"error": "Performance history unavailable."})


def _format_weekly_overview(weekly_summary: Dict, activities_data: Dict, cutoff_date: datetime) -> List[Dict]:
    """Format weekly overview section as list of week objects.

    Args:
        weekly_summary: Weekly summary data
        activities_data: Completed activities data with CTL/ATL
        cutoff_date: Date to filter from

    Returns:
        List of week dictionaries
    """
    weeks_list = []

    # Get weeks within date range, sorted by date descending
    weeks = []
    for week_start, data in weekly_summary.get("weekly_summary", {}).items():
        week_date = datetime.fromisoformat(week_start)
        if week_date >= cutoff_date:
            weeks.append((week_date, week_start, data))

    weeks.sort(reverse=True)  # Most recent first

    if not weeks:
        return []

    for week_date, week_start, data in weeks:
        # Get CTL/ATL from last activity of the week
        ctl, atl = _get_training_load_for_week(activities_data, week_date)

        # Build week object
        week_obj = {
            "start": week_start,
            "workouts": data.get('workout_count', 0),
            "hours": round(data.get('total_time_hours', 0), 1),
            "tss": int(data.get('total_tss', 0))
        }

        # Add CTL/ATL if available
        if ctl is not None:
            week_obj["ctl"] = int(ctl)
        if atl is not None:
            week_obj["atl"] = int(atl)

        # Zone distribution as array [z1, z2, z3, z4, z5]
        zone_times = data.get('total_time_in_zones', {})
        if zone_times:
            zones = []
            for i in range(1, 6):  # Z1-Z5
                zone_key = f'zone_{i}'
                hours = zone_times.get(zone_key, 0) / 3600
                zones.append(round(hours, 1))
            week_obj["zones"] = zones

        weeks_list.append(week_obj)

    return weeks_list


def _format_workout_log(workout_index: Dict, cutoff_date: datetime) -> List[Dict]:
    """Format detailed workout log section as list of workout objects (past only).

    Args:
        workout_index: Workout index data with planned vs actual
        cutoff_date: Date to filter from (past cutoff)

    Returns:
        List of workout dictionaries for past workouts only
    """
    workouts_list = []
    today = datetime.now()

    # Get dates within range (cutoff_date to today), sorted descending
    dates = []
    for date_str in workout_index.get("by_date", {}).keys():
        date = datetime.fromisoformat(date_str)
        # Only include past workouts (from cutoff to today, inclusive)
        if cutoff_date <= date <= today:
            dates.append((date, date_str))

    dates.sort(reverse=True)  # Most recent first

    if not dates:
        return []

    for date, date_str in dates:
        day_data = workout_index["by_date"][date_str]
        planned = day_data.get("planned", [])
        actual = day_data.get("actual", [])

        # Filter out empty workouts
        planned = [p for p in planned if p and p.get("name")]
        actual = [a for a in actual if a and a.get("activity_id")]

        # Skip days with no planned or actual workouts
        if not planned and not actual:
            continue

        # Track which actual workouts have been matched
        matched_activity_ids = set()

        # Process planned workouts
        for planned_workout in planned:
            workout_obj = {
                "date": date_str,
                "planned": {
                    "name": planned_workout.get("name", "Unnamed workout"),
                    "tss": int(planned_workout.get("planned_tss", 0)),
                    "min": planned_workout.get("planned_duration_seconds", 0) // 60
                }
            }

            # Find matching actual workout if completed
            if planned_workout.get("completed", False):
                completed_activity_id = planned_workout.get("completed_activity_id")
                matching_actual = next(
                    (a for a in actual if a.get("activity_id") == completed_activity_id),
                    None
                )

                if matching_actual:
                    matched_activity_ids.add(completed_activity_id)
                    workout_obj["actual"] = {
                        "tss": int(matching_actual.get("actual_tss", 0)),
                        "min": matching_actual.get("actual_duration_seconds", 0) // 60,
                        "completion": round(matching_actual.get("completion_percentage", 100), 1)
                    }
                else:
                    workout_obj["actual"] = {"completed": True}
            else:
                workout_obj["actual"] = {"completed": False}

            workouts_list.append(workout_obj)

        # Add unplanned workouts (actual workouts that didn't match any planned workout)
        for activity in actual:
            activity_id = activity.get("activity_id")
            if activity_id not in matched_activity_ids:
                workout_obj = {
                    "date": date_str,
                    "planned": None,
                    "actual": {
                        "type": activity.get("type", "Ride"),
                        "tss": int(activity.get("actual_tss", 0)),
                        "min": activity.get("actual_duration_seconds", 0) // 60
                    }
                }
                workouts_list.append(workout_obj)

    return workouts_list


def _calculate_summary_statistics(workout_index: Dict, cutoff_date: datetime) -> Dict:
    """Calculate and format summary statistics.

    Args:
        workout_index: Workout index data
        cutoff_date: Date to filter from

    Returns:
        Summary statistics dictionary
    """
    total_planned = 0
    total_completed = 0
    total_planned_tss = 0
    total_actual_tss = 0

    for date_str, day_data in workout_index.get("by_date", {}).items():
        date = datetime.fromisoformat(date_str)
        if date < cutoff_date:
            continue

        planned = day_data.get("planned", [])
        for workout in planned:
            if not workout:  # Skip empty workout dicts
                continue
            total_planned += 1
            total_planned_tss += workout.get("planned_tss", 0)
            if workout.get("completed", False):
                total_completed += 1
                # Add actual TSS from completed workouts only
                completed_activity_id = workout.get("completed_activity_id")
                if completed_activity_id:
                    # Find matching actual workout
                    actual = day_data.get("actual", [])
                    matching_actual = next(
                        (a for a in actual if a.get("activity_id") == completed_activity_id),
                        None
                    )
                    if matching_actual:
                        total_actual_tss += matching_actual.get("actual_tss", 0)

    summary = {}

    if total_planned > 0:
        compliance_rate = (total_completed / total_planned)
        summary["compliance"] = round(compliance_rate, 2)
        summary["compliance_text"] = f"{compliance_rate * 100:.1f}% ({total_completed} of {total_planned})"

        if total_planned_tss > 0 and total_actual_tss > 0:
            tss_adherence = (total_actual_tss / total_planned_tss)
            summary["tss_adherence"] = round(tss_adherence, 2)
            summary["tss_text"] = f"{tss_adherence * 100:.0f}%"
    else:
        summary["compliance"] = None
        summary["compliance_text"] = "No planned workouts"

    return summary


def _get_training_load_for_week(activities_data: Dict, week_start: datetime) -> tuple:
    """Get CTL and ATL for a given week.

    Args:
        activities_data: Completed activities data
        week_start: Start of the week

    Returns:
        Tuple of (CTL, ATL) or (None, None) if not found
    """
    # Get last activity of the week (week is 7 days from week_start)
    week_end = week_start + timedelta(days=7)

    activities = activities_data.get("activities", [])

    # Find activities in this week
    week_activities = []
    for activity in activities:
        activity_date = datetime.fromisoformat(activity.get("date", ""))
        if week_start <= activity_date < week_end:
            week_activities.append((activity_date, activity))

    if not week_activities:
        return None, None

    # Get the last activity in the week
    week_activities.sort(key=lambda x: x[0])
    last_activity = week_activities[-1][1]

    ctl = last_activity.get("chronic_training_load")
    atl = last_activity.get("acute_training_load")

    return ctl, atl


def _format_future_workouts(planned_events: List[Dict]) -> List[Dict]:
    """Format future planned workouts for the next 28 days.

    Args:
        planned_events: List of planned event dictionaries

    Returns:
        List of future workout dictionaries
    """
    future_workouts = []
    today = datetime.now()
    cutoff_future = today + timedelta(days=28)

    for event in planned_events:
        # Parse event date
        event_date_str = event.get("start_date_local", "")
        if not event_date_str:
            continue

        try:
            event_date = datetime.fromisoformat(event_date_str.split('T')[0])
        except (ValueError, AttributeError):
            continue

        # Only include events in next 28 days
        if today <= event_date <= cutoff_future:
            workout_obj = {
                "date": event_date.strftime("%Y-%m-%d"),
                "name": event.get("name", "Unnamed workout")
            }

            # Add TSS if available (icu_training_load)
            if event.get("icu_training_load"):
                workout_obj["tss"] = int(event.get("icu_training_load"))

            # Add duration if available (moving_time in seconds)
            if event.get("moving_time"):
                workout_obj["min"] = event.get("moving_time") // 60

            future_workouts.append(workout_obj)

    # Sort by date ascending (nearest first)
    future_workouts.sort(key=lambda x: x["date"])

    return future_workouts
