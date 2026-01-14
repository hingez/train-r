"""Workout matching service for linking planned events with completed activities."""
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger('train-r')


def match_workouts(
    planned_events: list[dict],
    completed_activities: list[dict],
    tss_threshold: float = 0.20
) -> tuple[list[dict], list[dict]]:
    """Match planned events with completed activities.

    Uses a two-phase approach:
    1. Use intervals.icu's paired_event_id (authoritative)
    2. Fuzzy matching for unlinked activities

    Args:
        planned_events: List of event dicts from intervals.icu
        completed_activities: List of activity dicts
        tss_threshold: TSS variance threshold for matching (default 20%)

    Returns:
        Tuple of (enhanced_activities, enhanced_events) with match links
    """
    logger.info(f"Matching {len(completed_activities)} activities with {len(planned_events)} events")

    # Phase 1: Use paired_event_id for authoritative matching
    matched_activities, matched_events, unmatched_activities, unmatched_events = \
        _use_paired_event_id(completed_activities, planned_events)

    logger.info(f"Phase 1 (paired_event_id): Matched {len(matched_activities)} activities")

    # Phase 2: Fuzzy matching for remaining activities
    fuzzy_matched_activities, fuzzy_matched_events = \
        _fuzzy_match(unmatched_activities, unmatched_events, tss_threshold)

    logger.info(f"Phase 2 (fuzzy match): Matched {len(fuzzy_matched_activities)} additional activities")

    # Combine results
    all_matched_activities = matched_activities + fuzzy_matched_activities + \
        [a for a in unmatched_activities if a['id'] not in {act['id'] for act in fuzzy_matched_activities}]

    all_matched_events = matched_events + fuzzy_matched_events + \
        [e for e in unmatched_events if e['id'] not in {evt['id'] for evt in fuzzy_matched_events}]

    total_matched = sum(1 for a in all_matched_activities if a.get('planned_event_id') is not None)
    logger.info(f"Total matched: {total_matched}/{len(completed_activities)} activities")

    return all_matched_activities, all_matched_events


def _use_paired_event_id(
    activities: list[dict],
    events: list[dict]
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Use intervals.icu's paired_event_id for authoritative matching.

    Args:
        activities: List of activity dicts
        events: List of event dicts

    Returns:
        Tuple of (matched_activities, matched_events, unmatched_activities, unmatched_events)
    """
    # Create event lookup by ID
    event_lookup = {event['id']: event for event in events}

    matched_activities = []
    unmatched_activities = []
    matched_event_ids = set()

    for activity in activities:
        paired_event_id = activity.get('paired_event_id')

        if paired_event_id and paired_event_id in event_lookup:
            # Found authoritative match
            activity['planned_event_id'] = paired_event_id
            activity['planned_match_confidence'] = 1.0  # Authoritative source
            matched_activities.append(activity)
            matched_event_ids.add(paired_event_id)
        else:
            # No paired event
            unmatched_activities.append(activity)

    # Update matched events with completion info
    matched_events = []
    unmatched_events = []

    for event in events:
        if event['id'] in matched_event_ids:
            # Find the activity that matched this event
            matching_activity = next(
                a for a in matched_activities
                if a.get('planned_event_id') == event['id']
            )
            event['completed'] = True
            event['completed_activity_id'] = matching_activity['id']
            event['completion_date'] = matching_activity['date']
            matched_events.append(event)
        else:
            event['completed'] = False
            unmatched_events.append(event)

    return matched_activities, matched_events, unmatched_activities, unmatched_events


def _fuzzy_match(
    activities: list[dict],
    events: list[dict],
    tss_threshold: float
) -> tuple[list[dict], list[dict]]:
    """Fuzzy match remaining activities to events.

    Matching criteria:
    1. Date (same day)
    2. Type (Ride, VirtualRide, etc.)
    3. TSS similarity (within threshold)

    Args:
        activities: List of unmatched activity dicts
        events: List of unmatched event dicts
        tss_threshold: TSS variance threshold (0.20 = 20%)

    Returns:
        Tuple of (matched_activities, matched_events)
    """
    # Index events by date
    events_by_date = {}
    for event in events:
        event_date = _extract_date(event.get('start_date_local', ''))
        if event_date:
            if event_date not in events_by_date:
                events_by_date[event_date] = []
            events_by_date[event_date].append(event)

    matched_activities = []
    matched_events = []
    matched_event_ids = set()

    for activity in activities:
        activity_date = _extract_date(activity.get('date', ''))
        if not activity_date or activity_date not in events_by_date:
            continue

        # Find best match among events on same date
        best_match = None
        best_confidence = 0.0

        for event in events_by_date[activity_date]:
            if event['id'] in matched_event_ids:
                continue  # Already matched

            confidence = _calculate_match_confidence(activity, event, tss_threshold)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = event

        # Only accept matches with confidence >= 0.50
        if best_match and best_confidence >= 0.50:
            activity['planned_event_id'] = best_match['id']
            activity['planned_match_confidence'] = best_confidence
            matched_activities.append(activity)

            best_match['completed'] = True
            best_match['completed_activity_id'] = activity['id']
            best_match['completion_date'] = activity['date']
            matched_events.append(best_match)

            matched_event_ids.add(best_match['id'])

    return matched_activities, matched_events


def _calculate_match_confidence(
    activity: dict,
    event: dict,
    tss_threshold: float
) -> float:
    """Calculate confidence score for activity-event match.

    Scoring:
    - Date + Type + TSS within 10% = 0.95
    - Date + Type + TSS within 20% = 0.85
    - Date + Type = 0.70
    - Date only = 0.50

    Args:
        activity: Activity dict
        event: Event dict
        tss_threshold: TSS variance threshold

    Returns:
        Confidence score (0.0 to 1.0)
    """
    score = 0.50  # Base score for same date (already checked)

    # Check type match
    activity_type = activity.get('type', '').lower()
    event_type = event.get('type', '').lower()

    type_match = activity_type == event_type or \
        (activity_type in ['ride', 'virtualride'] and event_type in ['ride', 'virtualride'])

    if not type_match:
        return 0.50  # Date only

    score = 0.70  # Date + Type

    # Check TSS similarity
    activity_tss = activity.get('training_stress_score')
    event_tss = event.get('icu_training_load')

    if activity_tss and event_tss and event_tss > 0:
        tss_variance = abs(activity_tss - event_tss) / event_tss

        if tss_variance <= 0.10:  # Within 10%
            score = 0.95
        elif tss_variance <= tss_threshold:  # Within threshold (default 20%)
            score = 0.85

    return score


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
        # Handle both date and datetime formats
        if 'T' in date_str:
            return date_str.split('T')[0]
        return date_str[:10]
    except Exception:
        return None
