"""Read a user's profile and print basic demographic info.

Usage:
    export TIDEPOOL_USERNAME=your@email.com
    export TIDEPOOL_PASSWORD=yourpassword
    export TIDEPOOL_USER_ID=your-user-id
    python examples/read_user_profile.py
"""

import os

from pytidepool import TidepoolClient, Environment

USERNAME = os.environ["TIDEPOOL_USERNAME"]
PASSWORD = os.environ["TIDEPOOL_PASSWORD"]
USER_ID = os.environ["TIDEPOOL_USER_ID"]

with TidepoolClient(
    environment=Environment.PRODUCTION,
    username=USERNAME,
    password=PASSWORD,
) as client:
    profile = client.metadata.get_profile(USER_ID)
    collections = client.metadata.get_collections()

print("=== User Profile ===")
print(f"  Name:        {profile.full_name or '(not set)'}")

if profile.patient:
    p = profile.patient
    print(f"  Birthday:    {p.birthday or '(not set)'}")
    print(f"  Diagnosis type: {p.diagnosis_type or '(not set)'}")

print(f"\nAvailable metadata collections: {', '.join(collections)}")
