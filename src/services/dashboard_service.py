"""Dashboard data service for Train-R.

This service loads and formats athlete data for the frontend dashboard,
providing data for 4 key performance charts.
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.config import AppConfig

logger = logging.getLogger('train-r')


class DashboardService:
    """Service for loading and formatting athlete dashboard data."""

    def __init__(self, config: AppConfig):
        """Initialize dashboard service.

        Args:
            config: Application configuration
        """
        self.config = config

    def get_dashboard_data(self) -> dict:
        """Load and format all dashboard data.

        Returns:
            Dict with keys: weekly_load, power_curve, zone_distribution, recent_activities
        """
        try:
            return {
                "weekly_load": self._get_weekly_load(),
                "power_curve": self._get_power_curve(),
                "zone_distribution": self._get_zone_dist(),
                "recent_activities": self._get_recent()
            }
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}", exc_info=True)
            # Return empty structure on error
            return {
                "weekly_load": [],
                "power_curve": {"thirty_day": [], "all_time": []},
                "zone_distribution": [],
                "recent_activities": []
            }

    def _get_weekly_load(self) -> list[dict]:
        """Get weekly training load for last 52 weeks (1 year).

        Returns:
            List of weekly load dicts with keys:
            - week_start: ISO date string
            - total_tss: Training stress score
            - total_time_hours: Training time in hours
            - total_distance_km: Distance in km
            - workout_count: Number of workouts
            - ctl: Chronic Training Load (fitness) at end of week
        """
        # Try new structure first, fall back to old
        weekly_summary_path = self.config.athlete_data_dir / "processed" / "weekly_summary.json"
        if not weekly_summary_path.exists():
            weekly_summary_path = self.config.athlete_data_dir / "athlete_weekly_summary.json"

        if not weekly_summary_path.exists():
            logger.warning(f"Weekly summary file not found: {weekly_summary_path}")
            return []

        try:
            with open(weekly_summary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            weekly_summary = data.get("weekly_summary", {})
            
            # Calculate CTL map (date -> ctl value)
            ctl_map = self._calculate_daily_ctl()

            # Calculate the start date for 52 weeks ago
            # Find the most recent week start to anchor
            if not weekly_summary:
                return []

            # We can use today to anchor, but better to use the latest data point or simply today relative
            # Let's align to Monday of the current week for consistency or just use data keys
            # For simplicity, we'll iterate back 52 weeks from the current week
            
            today = datetime.now()
            # Find closest Monday 
            current_week_start = today - timedelta(days=today.weekday())
            current_week_start = current_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            
            weeks = []
            
            # Generate last 52 weeks
            for i in range(52):
                week_date = current_week_start - timedelta(weeks=i)
                week_key = week_date.strftime("%Y-%m-%d")
                
                week_data = weekly_summary.get(week_key, {})
                
                # Get CTL for the end of this week (Sunday)
                # week_date is Monday. Sunday is +6 days.
                week_end_date = week_date + timedelta(days=6)
                week_end_key = week_end_date.strftime("%Y-%m-%d")
                
                # Find closest CTL value (if exact date missing, look back a few days or use last known)
                # Simple approach: look for exact match or use 0
                ctl_val = ctl_map.get(week_end_key, 0)
                
                # Fallback: if no CTL for Sunday, try finding most recent CTL before or on that date
                if ctl_val == 0 and ctl_map:
                     # Get all dates sorted
                     sorted_dates = sorted(ctl_map.keys())
                     # efficient search or simple iteration for now since dataset is small
                     last_valid_ctl = 0
                     for d_str in sorted_dates:
                         if d_str > week_end_key:
                             break
                         last_valid_ctl = ctl_map[d_str]
                     ctl_val = last_valid_ctl

                weeks.append({
                    "week_start": week_key,
                    "total_tss": week_data.get("total_tss", 0),
                    "total_time_hours": week_data.get("total_time_hours", 0),
                    "total_distance_km": week_data.get("total_distance_km", 0),
                    "workout_count": week_data.get("workout_count", 0),
                    "ctl": round(ctl_val, 1)
                })

            # Reverse to get chronological order (oldest first)
            weeks.reverse()
            return weeks

        except Exception as e:
            logger.error(f"Error loading weekly load data: {e}", exc_info=True)
            return []

    def _calculate_daily_ctl(self) -> dict:
        """Calculate daily CTL from workout history.

        Returns:
            Dict mapping date string ("YYYY-MM-DD") to CTL value.
        """
        # Try new structure first, fall back to old
        workout_history_path = self.config.athlete_data_dir / "raw" / "completed_activities.json"
        if not workout_history_path.exists():
            workout_history_path = self.config.athlete_data_dir / "athlete_workout_history.json"

        if not workout_history_path.exists():
            return {}
            
        try:
            with open(workout_history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Support both old and new format
            workout_history = data.get("activities", data.get("workout_history", []))
            
            # Aggregate TSS by day
            daily_tss = {}
            for w in workout_history:
                date_str = w.get("date", "").split("T")[0] # Simple date extraction
                tss = w.get("training_stress_score", 0) or 0
                daily_tss[date_str] = daily_tss.get(date_str, 0) + tss
                
            if not daily_tss:
                return {}
                
            # Sort dates
            sorted_dates = sorted(daily_tss.keys())
            if not sorted_dates:
                return {}
                
            # Calculate CTL over time
            # Start from first day, iterate to today (or last recorded day)
            # Fill in missing days with 0 TSS
            
            start_date = datetime.strptime(sorted_dates[0], "%Y-%m-%d")
            end_date = datetime.now() 
            
            curr_date = start_date
            ctl = 0
            time_constant = 42
            ctl_map = {}
            
            while curr_date <= end_date:
                curr_date_str = curr_date.strftime("%Y-%m-%d")
                
                day_tss = daily_tss.get(curr_date_str, 0)
                
                # CTL Formula: CTL_today = CTL_yesterday + (TSS_today - CTL_yesterday) / 42
                if ctl == 0 and day_tss > 0:
                     # Initial seed
                     ctl = day_tss
                else:
                     ctl = ctl + (day_tss - ctl) / time_constant
                
                ctl_map[curr_date_str] = ctl
                
                curr_date += timedelta(days=1)
                
            return ctl_map
            
        except Exception as e:
            logger.error(f"Error calculating CTL: {e}")
            return {}

    def _get_power_curve(self) -> dict:
        """Get power curves for both 30-day and all-time.

        Returns:
            Dict with keys:
            - thirty_day: List of power curve points for 30-day max
            - all_time: List of power curve points for all-time max
            Each point contains: duration, duration_seconds, watts
        """
        # Try new structure first, fall back to old
        power_history_path = self.config.athlete_data_dir / "raw" / "power_curves.json"
        if not power_history_path.exists():
            power_history_path = self.config.athlete_data_dir / "athlete_power_history.json"

        if not power_history_path.exists():
            logger.warning(f"Power history file not found: {power_history_path}")
            return {"thirty_day": [], "all_time": []}

        try:
            with open(power_history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            max_power = data.get("max_power", {})
            power_30_day = max_power.get("30_day", {})
            power_all_time = max_power.get("all_time", {})

            # Transform 30-day data to frontend format
            thirty_day_points = []
            for duration_key, watts in power_30_day.items():
                duration_secs = self._parse_duration_key(duration_key)
                if duration_secs is not None and watts is not None:
                    thirty_day_points.append({
                        "duration": self._format_duration(duration_secs),
                        "duration_seconds": duration_secs,
                        "watts": watts
                    })

            # Transform all-time data to frontend format
            all_time_points = []
            for duration_key, watts in power_all_time.items():
                duration_secs = self._parse_duration_key(duration_key)
                if duration_secs is not None and watts is not None:
                    all_time_points.append({
                        "duration": self._format_duration(duration_secs),
                        "duration_seconds": duration_secs,
                        "watts": watts
                    })

            return {
                "thirty_day": thirty_day_points,
                "all_time": all_time_points
            }

        except Exception as e:
            logger.error(f"Error loading power curve data: {e}", exc_info=True)
            return {"thirty_day": [], "all_time": []}

    def _get_zone_dist(self) -> list[dict]:
        """Get zone distribution by week for last 13 weeks.

        Returns:
            List of weekly zone distribution dicts with keys:
            - week_start: ISO date string
            - zone_1_hours: Hours in zone 1
            - zone_2_hours: Hours in zone 2
            - zone_3_hours: Hours in zone 3
            - zone_4_hours: Hours in zone 4
            - zone_5_hours: Hours in zone 5
        """
        # Try new structure first, fall back to old
        weekly_summary_path = self.config.athlete_data_dir / "processed" / "weekly_summary.json"
        if not weekly_summary_path.exists():
            weekly_summary_path = self.config.athlete_data_dir / "athlete_weekly_summary.json"

        if not weekly_summary_path.exists():
            logger.warning(f"Weekly summary file not found: {weekly_summary_path}")
            return []

        try:
            with open(weekly_summary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            weekly_summary = data.get("weekly_summary", {})

            # Get last 13 weeks (3 months)
            weeks = []
            for week_key in sorted(weekly_summary.keys(), reverse=True)[:13]:
                week_data = weekly_summary[week_key]
                time_in_zones = week_data.get("total_time_in_zones", {})

                weeks.append({
                    "week_start": week_data.get("week_start"),
                    "zone_1_hours": round(time_in_zones.get("zone_1", 0) / 3600, 2),
                    "zone_2_hours": round(time_in_zones.get("zone_2", 0) / 3600, 2),
                    "zone_3_hours": round(time_in_zones.get("zone_3", 0) / 3600, 2),
                    "zone_4_hours": round(time_in_zones.get("zone_4", 0) / 3600, 2),
                    "zone_5_hours": round(time_in_zones.get("zone_5", 0) / 3600, 2)
                })

            # Reverse to get chronological order (oldest first)
            weeks.reverse()
            return weeks

        except Exception as e:
            logger.error(f"Error loading zone distribution data: {e}", exc_info=True)
            return []

    def _get_recent(self) -> list[dict]:
        """Get last 10 activities.

        Returns:
            List of recent activity dicts with keys:
            - date: ISO date string
            - name: Activity name
            - duration: Duration in seconds
            - tss: Training stress score
            - np: Normalized power
            - if: Intensity factor
            - distance_km: Distance in km
        """
        # Try new structure first, fall back to old
        workout_history_path = self.config.athlete_data_dir / "raw" / "completed_activities.json"
        if not workout_history_path.exists():
            workout_history_path = self.config.athlete_data_dir / "athlete_workout_history.json"

        if not workout_history_path.exists():
            logger.warning(f"Workout history file not found: {workout_history_path}")
            return []

        try:
            with open(workout_history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Support both old and new format
            workout_history = data.get("activities", data.get("workout_history", []))

            # Get last 10 activities (already sorted newest first)
            recent = []
            for workout in workout_history[:10]:
                # Calculate distance in km if available
                distance_km = None
                distance_meters = workout.get("distance_meters")
                if distance_meters is not None:
                    distance_km = round(distance_meters / 1000, 2)

                recent.append({
                    "date": workout.get("date"),
                    "name": workout.get("name"),
                    "duration": workout.get("duration_seconds"),
                    "tss": workout.get("training_stress_score"),
                    "np": workout.get("normalized_power_watts"),
                    "avg_power": workout.get("avg_power_watts"),
                    "if": workout.get("intensity_factor"),
                    "distance_km": distance_km
                })

            return recent

        except Exception as e:
            logger.error(f"Error loading recent activities: {e}", exc_info=True)
            return []

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string (e.g., "5s", "1min", "20min", "1h")
        """
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}min"
        else:
            hours = seconds // 3600
            return f"{hours}h"

    def _parse_duration_key(self, duration_key: str) -> Optional[int]:
        """Parse duration key to seconds.

        Args:
            duration_key: Duration key (e.g., "15_seconds", "1_minutes", "1_hours")

        Returns:
            Duration in seconds, or None if parse fails
        """
        try:
            # Split on underscore to get value and unit
            parts = duration_key.rsplit("_", 1)
            if len(parts) != 2:
                return None

            value_str, unit = parts
            value = int(value_str)

            # Convert to seconds based on unit
            if unit == "seconds":
                return value
            elif unit == "minutes":
                return value * 60
            elif unit == "hours":
                return value * 3600
            else:
                logger.warning(f"Unknown duration unit: {unit}")
                return None

        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse duration key '{duration_key}': {e}")
            return None
