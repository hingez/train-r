"""Quick test script to verify upload functionality."""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.integrations.intervals import IntervalsClient

load_dotenv()

# Get credentials
api_key = os.getenv("INTERVALS_API_KEY")

# Initialize uploader - use athlete_id 0 (means "use athlete associated with API key")
intervals_client = IntervalsClient(api_key, athlete_id=None)

# Test connection first
print("Testing connection...")
if not intervals_client.test_connection():
    print("❌ Connection failed")
    exit(1)
print("✓ Connection successful")

# Upload test workout for tomorrow at 9 AM
workout_file = "data/created_workouts/test_workout.zwo"
target_date = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0)
target_date_str = target_date.strftime("%Y-%m-%dT%H:%M:%S")

print(f"\nUploading {workout_file}...")
print(f"Target date: {target_date_str}")

try:
    response = intervals_client.upload_workout(
        file_path=workout_file,
        start_date=target_date_str,
        external_id="test-upload-001"
    )

    print("\n✓ Upload successful!")
    print(f"Event ID: {response.get('id', 'N/A')}")
    print(f"Name: {response.get('name', 'N/A')}")
    print(f"Category: {response.get('category', 'N/A')}")

except Exception as e:
    print(f"\n❌ Upload failed: {e}")
    # Try to get more details if it's a requests exception
    if hasattr(e, 'response') and e.response is not None:
        try:
            print(f"Response body: {e.response.text}")
        except:
            pass
    exit(1)
