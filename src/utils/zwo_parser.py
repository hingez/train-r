"""ZWO workout file parser.

Parses ZWO XML workout files into structured segment data for visualization.
"""
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any

logger = logging.getLogger('train-r')


def calculate_training_zone(power_percent: float) -> str:
    """Calculate training zone based on % of FTP.

    Args:
        power_percent: Power as percentage of FTP (e.g., 95.0 for 95%)

    Returns:
        Training zone string (Z1-Z7)
    """
    if power_percent <= 55:
        return "Z1"
    elif power_percent <= 75:
        return "Z2"
    elif power_percent <= 87:
        return "Z3"
    elif power_percent <= 94:
        return "Z4"
    elif power_percent <= 105:
        return "Z5"
    elif power_percent <= 120:
        return "Z6"
    else:
        return "Z7"


def map_zone_to_workout_zone(training_zone: str, element_type: str) -> str:
    """Map training zone and element type to workout zone.

    Args:
        training_zone: Training zone (Z1-Z7)
        element_type: XML element type (Warmup, Cooldown, SteadyState, etc.)

    Returns:
        Workout zone string
    """
    # Override based on element type
    if element_type == "Warmup":
        return "warmup"
    elif element_type == "Cooldown":
        return "cooldown"

    # Map by training zone
    zone_map = {
        "Z1": "recovery",
        "Z2": "endurance",
        "Z3": "tempo",
        "Z4": "sweetspot",
        "Z5": "threshold",
        "Z6": "vo2max",
        "Z7": "vo2max"
    }
    return zone_map.get(training_zone, "endurance")


def format_time(seconds: int) -> str:
    """Format seconds to MM:SS or HH:MM:SS.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def determine_granularity(total_duration: int) -> int:
    """Determine segment granularity based on workout duration.

    Args:
        total_duration: Total workout duration in seconds

    Returns:
        Segment size in seconds
    """
    # Short workouts: 30-second segments
    if total_duration < 1800:  # < 30 minutes
        return 30
    # Medium workouts: 60-second segments
    elif total_duration < 5400:  # < 90 minutes
        return 60
    # Long workouts: 2-minute segments
    else:
        return 120


def parse_zwo_content(zwo_content: str, ftp: int) -> Dict[str, Any]:
    """Parse ZWO XML content into structured workout data.

    Args:
        zwo_content: ZWO XML file content
        ftp: Athlete's FTP in watts

    Returns:
        Dictionary with workout segments and metadata

    Raises:
        ValueError: If ZWO content is invalid
    """
    try:
        root = ET.fromstring(zwo_content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML content: {e}")

    # Extract metadata
    name_elem = root.find("name")
    desc_elem = root.find("description")
    workout_name = name_elem.text if name_elem is not None else "Workout"
    description = desc_elem.text if desc_elem is not None else ""

    # Find workout element
    workout_elem = root.find("workout")
    if workout_elem is None:
        raise ValueError("No <workout> element found in ZWO file")

    # First pass: calculate total duration
    total_duration = 0
    for elem in workout_elem:
        if elem.tag in ["Warmup", "Cooldown", "SteadyState", "Ramp", "FreeRide"]:
            duration = int(elem.get("Duration", 0))
            total_duration += duration
        elif elem.tag == "IntervalsT":
            # IntervalsT contains repeated intervals
            repeat = int(elem.get("Repeat", 1))
            on_duration = int(elem.get("OnDuration", 0))
            off_duration = int(elem.get("OffDuration", 0))
            total_duration += repeat * (on_duration + off_duration)

    # Determine granularity
    granularity = determine_granularity(total_duration)
    logger.info(f"Parsing workout: {workout_name}, Duration: {total_duration}s, Granularity: {granularity}s")

    # Second pass: create segments
    segments: List[Dict[str, Any]] = []
    current_time = 0

    for elem in workout_elem:
        elem_type = elem.tag

        if elem_type == "Warmup":
            duration = int(elem.get("Duration", 0))
            power_low = float(elem.get("PowerLow", 0.4))
            power_high = float(elem.get("PowerHigh", 0.75))

            # Break into segments with ramping power
            num_segments = max(1, duration // granularity)
            segment_duration = duration // num_segments

            for i in range(num_segments):
                # Interpolate power
                ratio = i / max(1, num_segments - 1) if num_segments > 1 else 0
                power_percent = power_low + (power_high - power_low) * ratio
                power = int(ftp * power_percent)
                power_pct = power_percent * 100

                segments.append({
                    "time": format_time(current_time),
                    "duration": segment_duration,
                    "power": power,
                    "zone": "warmup",
                    "trainingZone": calculate_training_zone(power_pct),
                    "label": "Warmup" if i == 0 else None
                })
                current_time += segment_duration

        elif elem_type == "Cooldown":
            duration = int(elem.get("Duration", 0))
            power_low = float(elem.get("PowerLow", 0.75))
            power_high = float(elem.get("PowerHigh", 0.3))

            # Break into segments with ramping power
            num_segments = max(1, duration // granularity)
            segment_duration = duration // num_segments

            for i in range(num_segments):
                # Interpolate power (high to low)
                ratio = i / max(1, num_segments - 1) if num_segments > 1 else 0
                power_percent = power_low + (power_high - power_low) * ratio
                power = int(ftp * power_percent)
                power_pct = power_percent * 100

                segments.append({
                    "time": format_time(current_time),
                    "duration": segment_duration,
                    "power": power,
                    "zone": "cooldown",
                    "trainingZone": calculate_training_zone(power_pct),
                    "label": "Cooldown" if i == 0 else None
                })
                current_time += segment_duration

        elif elem_type == "SteadyState":
            duration = int(elem.get("Duration", 0))
            power_percent = float(elem.get("Power", 0.75))
            power = int(ftp * power_percent)
            power_pct = power_percent * 100

            training_zone = calculate_training_zone(power_pct)
            workout_zone = map_zone_to_workout_zone(training_zone, elem_type)

            # Determine if this is a recovery segment (low power)
            if power_pct <= 60:
                workout_zone = "recovery"
                label = "Recovery"
            else:
                # Count existing intervals to number them
                interval_count = sum(1 for s in segments if (s.get("label") or "").startswith("Interval"))
                label = f"Interval {interval_count + 1}"

            # Break into segments
            num_segments = max(1, duration // granularity)
            segment_duration = duration // num_segments

            for i in range(num_segments):
                segments.append({
                    "time": format_time(current_time),
                    "duration": segment_duration,
                    "power": power,
                    "zone": workout_zone,
                    "trainingZone": training_zone,
                    "label": label if i == 0 else None
                })
                current_time += segment_duration

        elif elem_type == "Ramp":
            duration = int(elem.get("Duration", 0))
            power_low = float(elem.get("PowerLow", 0.5))
            power_high = float(elem.get("PowerHigh", 0.95))

            # Break into segments with ramping power
            num_segments = max(1, duration // granularity)
            segment_duration = duration // num_segments

            for i in range(num_segments):
                # Interpolate power
                ratio = i / max(1, num_segments - 1) if num_segments > 1 else 0
                power_percent = power_low + (power_high - power_low) * ratio
                power = int(ftp * power_percent)
                power_pct = power_percent * 100

                training_zone = calculate_training_zone(power_pct)
                workout_zone = map_zone_to_workout_zone(training_zone, elem_type)

                segments.append({
                    "time": format_time(current_time),
                    "duration": segment_duration,
                    "power": power,
                    "zone": workout_zone,
                    "trainingZone": training_zone,
                    "label": "Ramp" if i == 0 else None
                })
                current_time += segment_duration

        elif elem_type == "IntervalsT":
            # Repeated intervals (e.g., 5x3min @ 120% with 2min recovery)
            repeat = int(elem.get("Repeat", 1))
            on_duration = int(elem.get("OnDuration", 0))
            off_duration = int(elem.get("OffDuration", 0))
            on_power = float(elem.get("OnPower", 1.0))
            off_power = float(elem.get("OffPower", 0.5))

            for rep in range(repeat):
                # ON interval
                power = int(ftp * on_power)
                power_pct = on_power * 100
                training_zone = calculate_training_zone(power_pct)
                workout_zone = map_zone_to_workout_zone(training_zone, elem_type)

                num_segments = max(1, on_duration // granularity)
                segment_duration = on_duration // num_segments

                for i in range(num_segments):
                    segments.append({
                        "time": format_time(current_time),
                        "duration": segment_duration,
                        "power": power,
                        "zone": workout_zone,
                        "trainingZone": training_zone,
                        "label": f"Interval {rep + 1}" if i == 0 else None
                    })
                    current_time += segment_duration

                # OFF interval (recovery)
                if off_duration > 0:
                    power = int(ftp * off_power)
                    power_pct = off_power * 100
                    training_zone = calculate_training_zone(power_pct)

                    num_segments = max(1, off_duration // granularity)
                    segment_duration = off_duration // num_segments

                    for i in range(num_segments):
                        segments.append({
                            "time": format_time(current_time),
                            "duration": segment_duration,
                            "power": power,
                            "zone": "recovery",
                            "trainingZone": training_zone,
                            "label": "Recovery" if i == 0 else None
                        })
                        current_time += segment_duration

        elif elem_type == "FreeRide":
            # Free ride segments (no specific power target)
            duration = int(elem.get("Duration", 0))
            # Use a default moderate power for visualization
            power = int(ftp * 0.65)
            power_pct = 65.0

            training_zone = calculate_training_zone(power_pct)
            workout_zone = map_zone_to_workout_zone(training_zone, elem_type)

            num_segments = max(1, duration // granularity)
            segment_duration = duration // num_segments

            for i in range(num_segments):
                segments.append({
                    "time": format_time(current_time),
                    "duration": segment_duration,
                    "power": power,
                    "zone": workout_zone,
                    "trainingZone": training_zone,
                    "label": "Free Ride" if i == 0 else None
                })
                current_time += segment_duration

    return {
        "segments": segments,
        "ftp": ftp,
        "totalDuration": total_duration,
        "workoutName": workout_name,
        "description": description
    }


def parse_zwo_file(file_path: str, ftp: int) -> Dict[str, Any]:
    """Parse ZWO file from filesystem.

    Args:
        file_path: Path to ZWO file
        ftp: Athlete's FTP in watts

    Returns:
        Dictionary with workout segments and metadata
    """
    with open(file_path, 'r') as f:
        zwo_content = f.read()

    return parse_zwo_content(zwo_content, ftp)
