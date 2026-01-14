"""Index builder service for creating fast workout lookups."""
import logging
from datetime import datetime
from collections import defaultdict
from typing import Optional

logger = logging.getLogger('train-r')


def build_workout_index(
    activities: list[dict],
    events: list[dict]
) -> dict:
    """Build comprehensive workout index for fast lookups.

    Creates indices by:
    - Date (planned vs actual for each day)
    - Week (compliance and adherence metrics)
    - Type (workout type grouping)

    Args:
        activities: List of activity dicts (with planned_event_id if matched)
        events: List of event dicts (with completed flags)

    Returns:
        Index dict with by_date, by_week, by_type lookups
    """
    logger.info("Building workout index from activities and events")

    index = {
        "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "by_date": build_date_index(activities, events),
        "by_week": build_week_index(activities, events),
        "by_type": build_type_index(activities, events)
    }

    logger.info(f"Index built: {len(index['by_date'])} dates, {len(index['by_week'])} weeks, {len(index['by_type'])} types")
    return index


def build_date_index(
    activities: list[dict],
    events: list[dict]
) -> dict:
    """Group workouts by date with planned vs actual.

    Args:
        activities: List of activity dicts
        events: List of event dicts

    Returns:
        Dict mapping date -> {planned: [...], actual: [...]}
    """
    date_index = defaultdict(lambda: {"planned": [], "actual": []})

    # Add planned events
    for event in events:
        date = _extract_date(event.get('start_date_local', ''))
        if not date:
            continue

        date_index[date]["planned"].append({
            "event_id": event['id'],
            "name": event.get('name', ''),
            "type": event.get('type', ''),
            "planned_tss": event.get('icu_training_load'),
            "planned_duration_seconds": event.get('moving_time'),
            "completed": event.get('completed', False),
            "completed_activity_id": event.get('completed_activity_id')
        })

    # Add actual activities
    for activity in activities:
        date = _extract_date(activity.get('date', ''))
        if not date:
            continue

        matched_event_id = activity.get('planned_event_id')
        actual_tss = activity.get('training_stress_score')
        actual_duration = activity.get('duration_seconds')

        # Calculate variances if matched
        variance_tss = None
        variance_duration = None
        completion_percentage = None

        if matched_event_id:
            # Find the matching event
            matching_event = next(
                (e for e in events if e['id'] == matched_event_id),
                None
            )
            if matching_event:
                planned_tss = matching_event.get('icu_training_load')
                planned_duration = matching_event.get('moving_time')

                if actual_tss is not None and planned_tss:
                    variance_tss = actual_tss - planned_tss
                    completion_percentage = (actual_tss / planned_tss) * 100

                if actual_duration is not None and planned_duration:
                    variance_duration = actual_duration - planned_duration

        date_index[date]["actual"].append({
            "activity_id": activity['id'],
            "type": activity.get('type', ''),
            "actual_tss": actual_tss,
            "actual_duration_seconds": actual_duration,
            "matched_event_id": matched_event_id,
            "match_confidence": activity.get('planned_match_confidence'),
            "variance_tss": variance_tss,
            "variance_duration_seconds": variance_duration,
            "completion_percentage": round(completion_percentage, 1) if completion_percentage else None
        })

    return dict(date_index)


def build_week_index(
    activities: list[dict],
    events: list[dict]
) -> dict:
    """Aggregate workouts by week with compliance metrics.

    Args:
        activities: List of activity dicts
        events: List of event dicts

    Returns:
        Dict mapping ISO week -> summary metrics
    """
    week_index = defaultdict(lambda: {
        "week_start": None,
        "planned_tss": 0,
        "actual_tss": 0,
        "planned_workouts": 0,
        "completed_workouts": 0,
        "compliance_rate": 0.0,
        "tss_adherence": 0.0
    })

    # Aggregate planned events by week
    for event in events:
        week = _get_iso_week(event.get('start_date_local', ''))
        if not week:
            continue

        if not week_index[week]["week_start"]:
            week_index[week]["week_start"] = _get_week_start_date(week)

        planned_tss = event.get('icu_training_load', 0) or 0
        week_index[week]["planned_tss"] += planned_tss
        week_index[week]["planned_workouts"] += 1

        if event.get('completed', False):
            week_index[week]["completed_workouts"] += 1

    # Aggregate actual activities by week
    for activity in activities:
        week = _get_iso_week(activity.get('date', ''))
        if not week:
            continue

        actual_tss = activity.get('training_stress_score', 0) or 0
        week_index[week]["actual_tss"] += actual_tss

    # Calculate compliance and adherence rates
    for week_data in week_index.values():
        planned_workouts = week_data["planned_workouts"]
        completed_workouts = week_data["completed_workouts"]
        planned_tss = week_data["planned_tss"]
        actual_tss = week_data["actual_tss"]

        if planned_workouts > 0:
            week_data["compliance_rate"] = round(completed_workouts / planned_workouts, 3)

        if planned_tss > 0:
            week_data["tss_adherence"] = round(actual_tss / planned_tss, 3)

    return dict(week_index)


def build_type_index(
    activities: list[dict],
    events: list[dict]
) -> dict:
    """Group workouts by type.

    Args:
        activities: List of activity dicts
        events: List of event dicts

    Returns:
        Dict mapping workout type -> list of occurrences
    """
    type_index = defaultdict(list)

    # Index by event name/type for planned workouts
    for event in events:
        workout_name = event.get('name', 'Unknown')
        if not workout_name:
            workout_name = event.get('type', 'Unknown')

        date = _extract_date(event.get('start_date_local', ''))
        activity_id = event.get('completed_activity_id')

        type_index[workout_name].append({
            "date": date,
            "event_id": event['id'],
            "activity_id": activity_id,
            "completed": event.get('completed', False)
        })

    return dict(type_index)


def _extract_date(date_str: str) -> Optional[str]:
    """Extract YYYY-MM-DD date from datetime string.

    Args:
        date_str: Date or datetime string

    Returns:
        Date string in YYYY-MM-DD format, or None if invalid
    """
    if not date_str:
        return None

    try:
        if 'T' in date_str:
            return date_str.split('T')[0]
        return date_str[:10]
    except Exception:
        return None


def _get_iso_week(date_str: str) -> Optional[str]:
    """Get ISO week string (YYYY-WXX) from date string.

    Args:
        date_str: Date or datetime string

    Returns:
        ISO week string like "2026-W02", or None if invalid
    """
    date = _extract_date(date_str)
    if not date:
        return None

    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        year, week, _ = dt.isocalendar()
        return f"{year}-W{week:02d}"
    except Exception:
        return None


def _get_week_start_date(iso_week: str) -> Optional[str]:
    """Get the Monday date for an ISO week.

    Args:
        iso_week: ISO week string like "2026-W02"

    Returns:
        Monday date in YYYY-MM-DD format, or None if invalid
    """
    try:
        from datetime import timedelta

        year, week = iso_week.split('-W')
        year = int(year)
        week = int(week)

        # ISO week 1 is the week with the first Thursday
        jan_4 = datetime(year, 1, 4)
        week_1_monday = jan_4 - timedelta(days=jan_4.weekday())

        # Calculate target week's Monday
        target_monday = week_1_monday + timedelta(weeks=(week - 1))
        return target_monday.strftime("%Y-%m-%d")
    except Exception:
        return None
