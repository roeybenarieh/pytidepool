"""Print CGM and BGM time-in-range summary statistics.

Usage:
    export TIDEPOOL_USERNAME=your@email.com
    export TIDEPOOL_PASSWORD=yourpassword
    python examples/time_in_range_summary.py
"""

import os

from pytidepool import TidepoolClient, Environment

USERNAME = os.environ["TIDEPOOL_USERNAME"]
PASSWORD = os.environ["TIDEPOOL_PASSWORD"]

with TidepoolClient(
    environment=Environment.PRODUCTION,
    username=USERNAME,
    password=PASSWORD,
) as client:
    cgm = client.summary.get_cgm()
    bgm = client.summary.get_bgm()

# CGM summary
print("=== CGM Summary ===")
if not cgm.periods:
    print("  No CGM data available.")
else:
    for period_name in ("1d", "7d", "14d", "30d"):
        period = cgm.periods.get(period_name)
        if period is None:
            continue
        tir = period.time_in_range
        if tir is None:
            print(f"  {period_name:>4s}: no time-in-range data")
            continue
        target = tir.target_percent or 0.0
        low = tir.low_percent or 0.0
        high = tir.high_percent or 0.0
        print(
            f"  {period_name:>4s}:  in-range {target:.1f}%"
            f"  |  below {low:.1f}%"
            f"  |  above {high:.1f}%"
        )

# BGM summary
print("\n=== BGM Summary ===")
if not bgm.periods:
    print("  No BGM data available.")
else:
    for period_name in ("1d", "7d", "14d", "30d"):
        period = bgm.periods.get(period_name)
        if period is None:
            continue
        tir = period.time_in_range
        if tir is None:
            print(f"  {period_name:>4s}: no time-in-range data")
            continue
        target = tir.target_percent or 0.0
        low = tir.low_percent or 0.0
        high = tir.high_percent or 0.0
        print(
            f"  {period_name:>4s}:  in-range {target:.1f}%"
            f"  |  below {low:.1f}%"
            f"  |  above {high:.1f}%"
        )
