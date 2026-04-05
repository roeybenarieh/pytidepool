"""Plot CGM glucose readings as an annotated time-series chart.

Requires matplotlib:
    pip install matplotlib
    uv add matplotlib

Usage:
    export TIDEPOOL_USERNAME=your@email.com
    export TIDEPOOL_PASSWORD=yourpassword
    python examples/visualize_cgm.py

Optional env vars:
    TIDEPOOL_DAYS=7        # how many days of history to fetch (default: 14)
    TIDEPOOL_UNITS=mgdl    # display units: "mgdl" or "mmol" (default: mgdl)
"""

import os
from datetime import datetime, timedelta, timezone

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from pytidepool import TidepoolClient, Environment, DiabetesType
from pytidepool.models.data import CbgReading

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

USERNAME = os.environ["TIDEPOOL_USERNAME"]
PASSWORD = os.environ["TIDEPOOL_PASSWORD"]
DAYS = int(os.environ.get("TIDEPOOL_DAYS", "14"))
UNITS = os.environ.get("TIDEPOOL_UNITS", "mgdl").lower()

# Target range thresholds (mmol/L — converted below if needed)
LOW_MMOL = 3.9  # 70 mg/dL
HIGH_MMOL = 10.0  # 180 mg/dL

# ---------------------------------------------------------------------------
# Fetch data
# ---------------------------------------------------------------------------

print(f"Fetching {DAYS} days of CGM data…")

with TidepoolClient(
    environment=Environment.PRODUCTION,
    username=USERNAME,
    password=PASSWORD,
) as client:
    raw = client.data.get(
        data_types=[DiabetesType.CBG],
        start_date=datetime.now(timezone.utc) - timedelta(days=DAYS),
        end_date=datetime.now(timezone.utc),
    )

readings: list[CbgReading] = [r for r in raw if isinstance(r, CbgReading)]

if not readings:
    raise SystemExit("No CGM readings found for this account / time window.")

print(f"  {len(readings)} readings retrieved.")

# Sort by time
readings.sort(key=lambda r: r.time)

# ---------------------------------------------------------------------------
# Build plot arrays
# ---------------------------------------------------------------------------

times = [r.time for r in readings]

if UNITS == "mgdl":
    values = [r.value * 18.0182 for r in readings]
    unit_label = "mg/dL"
    low_threshold = LOW_MMOL * 18.0182
    high_threshold = HIGH_MMOL * 18.0182
    y_min, y_max = 40, 400
    y_ticks = [54, 70, 140, 180, 250, 300]
else:
    values = [r.value for r in readings]
    unit_label = "mmol/L"
    low_threshold = LOW_MMOL
    high_threshold = HIGH_MMOL
    y_min, y_max = 2.0, 22.0
    y_ticks = [3.0, 3.9, 7.8, 10.0, 13.9, 16.7]

# Assign a color to each point based on range
colors = []
for v in values:
    if v < low_threshold:
        colors.append("#e74c3c")  # red — below range
    elif v > high_threshold:
        colors.append("#f39c12")  # amber — above range
    else:
        colors.append("#27ae60")  # green — in range

# ---------------------------------------------------------------------------
# Time-in-range statistics
# ---------------------------------------------------------------------------

n = len(values)
n_low = sum(1 for v in values if v < low_threshold)
n_high = sum(1 for v in values if v > high_threshold)
n_in = n - n_low - n_high

pct_in = 100 * n_in / n
pct_low = 100 * n_low / n
pct_high = 100 * n_high / n

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(14, 5))

# Shaded target-range band
ax.axhspan(low_threshold, high_threshold, color="#27ae60", alpha=0.08, zorder=0)

# Threshold lines
ax.axhline(low_threshold, color="#e74c3c", linewidth=0.8, linestyle="--", alpha=0.7)
ax.axhline(high_threshold, color="#f39c12", linewidth=0.8, linestyle="--", alpha=0.7)

# CGM trace
ax.plot(times, values, color="#bdc3c7", linewidth=0.6, zorder=1)

# Coloured scatter on top
ax.scatter(times, values, c=colors, s=6, zorder=2, linewidths=0)

# Axes
ax.set_ylim(y_min, y_max)
ax.set_yticks(y_ticks)
ax.set_ylabel(unit_label, fontsize=11)
ax.set_xlabel("Date / time", fontsize=11)

# Date formatting on x-axis
locator = mdates.AutoDateLocator()
formatter = mdates.ConciseDateFormatter(locator)
ax.xaxis.set_major_locator(locator)
ax.xaxis.set_major_formatter(formatter)
fig.autofmt_xdate()

# Grid
ax.grid(axis="y", linewidth=0.4, alpha=0.5)
ax.set_axisbelow(True)

# Legend for ranges
patches = [
    mpatches.Patch(color="#e74c3c", label=f"Below range  ({pct_low:.0f}%)"),
    mpatches.Patch(color="#27ae60", label=f"In range  ({pct_in:.0f}%)"),
    mpatches.Patch(color="#f39c12", label=f"Above range  ({pct_high:.0f}%)"),
]
ax.legend(handles=patches, loc="upper right", fontsize=9, framealpha=0.9)

# Title
ax.set_title(
    f"CGM Glucose — last {DAYS} days  ({len(readings)} readings)",
    fontsize=13,
    pad=10,
)

plt.tight_layout()
plt.show()
