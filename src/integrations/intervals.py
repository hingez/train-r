"""Module for interacting with intervals.icu API."""
import base64
import os
import logging
from pathlib import Path
from typing import Optional
import requests
from datetime import datetime, timedelta

from src.config import AppConfig
from src.utils.retry import retry_with_backoff


class IntervalsClient:
    """Client for intervals.icu API - handles uploads and data retrieval."""

    def __init__(self, api_key: str, config: AppConfig, athlete_id: Optional[str] = None):
        """Initialize uploader with API key.

        Args:
            api_key: intervals.icu API key
            config: Application configuration
            athlete_id: intervals.icu athlete ID (optional, will use default from config if not provided)
        """
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key
        self.config = config
        self.athlete_id = athlete_id if athlete_id else config.default_athlete_id
        self.auth = ("API_KEY", api_key)

    def read_workout_file(self, file_path: str) -> str:
        """Read ZWO file contents and encode as base64.

        Args:
            file_path: Path to .zwo file

        Returns:
            Base64 encoded file contents

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a .zwo file
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() != ".zwo":
            raise ValueError(f"File must be a .zwo file, got: {path.suffix}")

        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def _build_and_upload_event(
        self,
        file_contents_base64: str,
        filename: str,
        start_date: str,
        external_id: Optional[str] = None
    ) -> dict:
        """Build event payload and upload to intervals.icu with retry logic.

        Args:
            file_contents_base64: Base64 encoded file contents
            filename: Filename for the workout
            start_date: Start date/time in ISO format (YYYY-MM-DDTHH:MM:SS)
            external_id: Optional external ID for tracking

        Returns:
            API response as dict (first event from array response)

        Raises:
            requests.HTTPError: If API request fails after all retries
        """
        # Build payload - must be an array for bulk endpoint
        event = {
            "category": "WORKOUT",
            "start_date_local": start_date,
            "type": "Ride",
            "filename": filename,
            "file_contents_base64": file_contents_base64
        }

        if external_id:
            event["external_id"] = external_id

        payload = [event]
        url = f"{self.config.intervals_base_url}/athlete/{self.athlete_id}/events/bulk"

        # Define custom retry logic for HTTP errors
        def should_retry(exception: Exception) -> bool:
            """Determine if HTTP error should be retried.

            Don't retry on client errors (4xx) except 429 (rate limit).
            """
            logger = logging.getLogger('train-r')
            if isinstance(exception, requests.HTTPError) and exception.response is not None:
                status_code = exception.response.status_code
                if 400 <= status_code < 500 and status_code != 429:
                    logger.error(f"Client error {status_code}, not retrying")
                    return False
            return True

        # Define the upload function for retry wrapper
        def make_upload_request() -> dict:
            response = requests.post(
                url,
                params={"upsert": True},
                json=payload,
                auth=self.auth,
                timeout=self.config.intervals_api_timeout
            )
            response.raise_for_status()
            result = response.json()
            # Return first event from array response
            return result[0] if isinstance(result, list) and result else result

        # Execute with retry logic
        return retry_with_backoff(
            func=make_upload_request,
            exception_types=(requests.RequestException, requests.HTTPError),
            operation_name="intervals.icu upload",
            should_retry_func=should_retry
        )

    def upload_workout_content(
        self,
        zwo_content: str,
        filename: str,
        start_date: str,
        external_id: Optional[str] = None
    ) -> dict:
        """Upload workout content directly to intervals.icu calendar.

        Args:
            zwo_content: ZWO file content as string
            filename: Filename for the workout
            start_date: Start date/time in ISO format (YYYY-MM-DDTHH:MM:SS)
            external_id: Optional external ID for tracking

        Returns:
            API response as dict (first event from array response)

        Raises:
            requests.HTTPError: If API request fails
        """
        # Base64 encode the content
        file_contents_base64 = base64.b64encode(zwo_content.encode('utf-8')).decode('utf-8')

        # Use shared upload logic
        return self._build_and_upload_event(file_contents_base64, filename, start_date, external_id)

    def upload_workout(
        self,
        file_path: str,
        start_date: str,
        external_id: Optional[str] = None
    ) -> dict:
        """Upload workout to intervals.icu calendar using bulk endpoint.

        Args:
            file_path: Path to .zwo workout file
            start_date: Start date/time in ISO format (YYYY-MM-DDTHH:MM:SS)
            external_id: Optional external ID for tracking

        Returns:
            API response as dict (first event from array response)

        Raises:
            requests.HTTPError: If API request fails
        """
        file_contents_base64 = self.read_workout_file(file_path)
        filename = Path(file_path).name

        # Use shared upload logic
        return self._build_and_upload_event(file_contents_base64, filename, start_date, external_id)

    def get_workout_history(
        self,
        oldest_date: Optional[str] = None,
        newest_date: Optional[str] = None
    ) -> list[dict]:
        """Retrieve completed activity history from intervals.icu.

        Uses the /activities endpoint which returns only completed activities
        with actual performance data (power, heart rate, etc.), not planned workouts.
        Automatically defaults to last 12 months if oldest_date not specified.
        Transforms field names to be universally understandable for LLM processing.

        Args:
            oldest_date: Start date in YYYY-MM-DD format (optional, defaults to 12 months ago)
            newest_date: End date in YYYY-MM-DD format (optional, defaults to today)

        Returns:
            List of transformed activity dicts with standardized field names

        Raises:
            requests.HTTPError: If API request fails
        """
        logger = logging.getLogger('train-r')

        # Default to configured lookback period if not specified
        if not oldest_date:
            lookback_ago = datetime.now() - timedelta(days=self.config.history_default_lookback_days)
            oldest_date = lookback_ago.strftime("%Y-%m-%d")

        if not newest_date:
            newest_date = datetime.now().strftime("%Y-%m-%d")

        # Use activities endpoint for completed rides only
        url = f"{self.config.intervals_base_url}/athlete/{self.athlete_id}/activities"
        params = {
            'oldest': oldest_date,
            'newest': newest_date
        }

        # Define the fetch function for retry wrapper
        def make_fetch_request() -> list[dict]:
            response = requests.get(
                url,
                params=params,
                auth=self.auth,
                timeout=self.config.intervals_api_timeout
            )
            response.raise_for_status()
            return response.json()

        # Execute with retry logic
        logger.info(f"Fetching activity history from intervals.icu (oldest={oldest_date}, newest={newest_date})")

        result = retry_with_backoff(
            func=make_fetch_request,
            exception_types=(requests.RequestException, requests.HTTPError),
            operation_name="intervals.icu fetch activities"
        )

        logger.info(f"Successfully fetched {len(result)} completed activities from intervals.icu")

        # Transform activities to use standardized field names
        transformed_activities = []
        for activity in result:
            transformed = {
                "date": activity.get("start_date_local"),
                "type": activity.get("type"),
                "duration_seconds": activity.get("moving_time"),
                "distance_meters": activity.get("distance"),
                "avg_power_watts": activity.get("icu_average_watts"),
                "normalized_power_watts": activity.get("icu_weighted_avg_watts"),
                "intensity_factor": activity.get("icu_intensity"),
                "training_stress_score": activity.get("icu_training_load"),
                "power_zone_times": activity.get("icu_zone_times"),
                "acute_training_load": activity.get("icu_atl"),
                "chronic_training_load": activity.get("icu_ctl")
            }
            transformed_activities.append(transformed)

        logger.info(f"Transformed {len(transformed_activities)} activities with standardized field names")
        return transformed_activities

    def get_power_curves(
        self,
        time_periods_months: Optional[list[int]] = None,
        durations_seconds: Optional[list[int]] = None,
        sport_type: str = "Ride"
    ) -> dict:
        """Retrieve aggregate power curves from intervals.icu.

        Gets best power outputs across all activities for specified time periods
        and durations. Useful for tracking fitness improvements over time.

        Args:
            time_periods_months: List of time periods in months (default: [1, 2, 3, 6, 12])
            durations_seconds: List of durations in seconds to retrieve power for
                             (default: [15, 30, 60, 120, 180, 300, 600, 900, 1200, 1800, 2700, 3600])
            sport_type: Sport type to filter activities (default: "Ride")

        Returns:
            Dict mapping time periods to power curves, e.g.:
            {
                "1_month": {"15_seconds": 450, "30_seconds": 420, ...},
                "2_months": {"15_seconds": 455, "30_seconds": 425, ...},
                ...
            }

        Raises:
            requests.HTTPError: If API request fails
        """
        logger = logging.getLogger('train-r')

        # Use configured defaults if not provided
        if time_periods_months is None:
            time_periods_months = self.config.power_curve_time_periods_months

        if durations_seconds is None:
            durations_seconds = self.config.power_curve_durations_seconds

        power_curves = {}

        for months in time_periods_months:
            # Calculate the date range for this time period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)  # Approximate month as 30 days

            # Use the activity-power-curves endpoint with empty ext parameter
            # API spec: /api/v1/athlete/{id}/activity-power-curves{ext}
            url = f"{self.config.intervals_base_url}/athlete/{self.athlete_id}/activity-power-curves"
            params = {
                'oldest': start_date.strftime("%Y-%m-%d"),
                'newest': end_date.strftime("%Y-%m-%d"),
                'type': sport_type,
                'secs': ','.join(str(s) for s in durations_seconds)
            }

            # Define the fetch function for retry wrapper
            def make_fetch_request() -> dict:
                response = requests.get(
                    url,
                    params=params,
                    auth=self.auth,
                    timeout=self.config.intervals_api_timeout
                )
                response.raise_for_status()
                return response.json()

            # Execute with retry logic
            logger.info(f"Fetching {months}-month power curve from intervals.icu")

            try:
                result = retry_with_backoff(
                    func=make_fetch_request,
                    exception_types=(requests.RequestException, requests.HTTPError),
                    operation_name=f"intervals.icu fetch {months}-month power curve"
                )

                # Transform the result to extract best power values for requested durations
                # The API returns: {secs: [15, 30, ...], curves: [{watts: [...]}, ...]}
                period_key = f"{months}_month" if months == 1 else f"{months}_months"
                power_curves[period_key] = {}

                # Extract best power for each duration across all activities
                if isinstance(result, dict) and 'secs' in result and 'curves' in result:
                    secs_array = result['secs']
                    curves = result['curves']

                    # For each duration, find the max watts across all activities
                    for idx, duration_secs in enumerate(secs_array):
                        # Format duration as human-readable key
                        if duration_secs < 60:
                            duration_key = f"{duration_secs}_seconds"
                        elif duration_secs < 3600:
                            duration_key = f"{duration_secs // 60}_minutes"
                        else:
                            duration_key = f"{duration_secs // 3600}_hours"

                        # Find max watts for this duration across all activities
                        max_watts = None
                        for curve in curves:
                            if 'watts' in curve and idx < len(curve['watts']):
                                watts = curve['watts'][idx]
                                if watts and (max_watts is None or watts > max_watts):
                                    max_watts = watts

                        power_curves[period_key][duration_key] = max_watts

                    logger.info(f"Successfully fetched {months}-month power curve with {len(power_curves[period_key])} data points")
                else:
                    # If response structure is different, log the structure for debugging
                    logger.warning(f"Unexpected response structure for {months}-month curve: {result.keys() if isinstance(result, dict) else type(result)}")
                    power_curves[period_key] = result

            except requests.HTTPError as e:
                logger.error(f"Failed to fetch {months}-month power curve: {str(e)}")
                # Continue with other time periods even if one fails
                period_key = f"{months}_month_max_power" if months == 1 else f"{months}_months_max_power"
                power_curves[period_key] = {"error": str(e)}

        logger.info(f"Retrieved power curves for {len(power_curves)} time periods")
        return power_curves

    def test_connection(self) -> bool:
        """Test API connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/athlete/{self.athlete_id}"
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False
