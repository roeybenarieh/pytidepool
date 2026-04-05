"""Fetch CGM glucose readings for the last 14 days.

Usage:
    export TIDEPOOL_USERNAME=your@email.com
    export TIDEPOOL_PASSWORD=yourpassword
    python examples/fetch_cgm_readings.py
"""

import os
from datetime import datetime, timedelta, timezone

from pytidepool import TidepoolClient, Environment, DiabetesType
from pytidepool.models.data import CbgReading

USERNAME = os.environ["TIDEPOOL_USERNAME"]
PASSWORD = os.environ["TIDEPOOL_PASSWORD"]

with TidepoolClient(
    environment=Environment.PRODUCTION,
    username=USERNAME,
    password=PASSWORD,
) as client:
    user_id = client.get_user_id()
    readings = client.data.get(
        user_id,
        data_types=[DiabetesType.CBG],
        start_date=datetime.now(timezone.utc) - timedelta(days=14),
        end_date=datetime.now(timezone.utc),
    )

print(f"Fetched {len(readings)} CGM readings over the last 14 days.\n")

for r in readings[:10]:
    assert isinstance(r, CbgReading)
    mmol = r.value
    mgdl = mmol * 18.0182
    print(f"  {r.time}  {mmol:.1f} mmol/L  ({mgdl:.0f} mg/dL)")

if len(readings) > 10:
    print(f"  ... and {len(readings) - 10} more")
