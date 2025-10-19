"""Module for uploading workouts to intervals.icu."""
import base64
import os
import time
import logging
from pathlib import Path
from typing import Optional
import requests
from datetime import datetime

from train_r.core.config import DEFAULT_ATHLETE_ID

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
RETRY_BACKOFF_MULTIPLIER = 2


class IntervalsUploader:
    """Handle workout uploads to intervals.icu via API."""

    BASE_URL = "https://intervals.icu/api/v1"

    def __init__(self, api_key: str, athlete_id: Optional[str] = None):
        """Initialize uploader with API key.

        Args:
            api_key: intervals.icu API key
            athlete_id: intervals.icu athlete ID (optional, will use default if not provided)
        """
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key
        self.athlete_id = athlete_id if athlete_id else DEFAULT_ATHLETE_ID
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
        logger = logging.getLogger('train-r')

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
        url = f"{self.BASE_URL}/athlete/{self.athlete_id}/events/bulk"

        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                # Make API request to bulk endpoint with upsert parameter
                response = requests.post(
                    url,
                    params={"upsert": True},
                    json=payload,
                    auth=self.auth,
                    timeout=30
                )

                response.raise_for_status()
                result = response.json()

                # If we had retries, log success
                if attempt > 0:
                    logger.info(f"Upload successful on attempt {attempt + 1}")

                # Return first event from array response
                return result[0] if isinstance(result, list) and result else result

            except (requests.RequestException, requests.HTTPError) as e:
                last_exception = e

                # Don't retry on client errors (4xx except 429)
                if isinstance(e, requests.HTTPError) and e.response is not None:
                    status_code = e.response.status_code
                    if 400 <= status_code < 500 and status_code != 429:
                        logger.error(f"Client error {status_code}, not retrying")
                        raise

                # Calculate backoff delay
                if attempt < MAX_RETRIES - 1:
                    delay = INITIAL_RETRY_DELAY * (RETRY_BACKOFF_MULTIPLIER ** attempt)
                    logger.warning(
                        f"Upload attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Upload failed after {MAX_RETRIES} attempts")

        # If we get here, all retries failed
        raise last_exception

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
