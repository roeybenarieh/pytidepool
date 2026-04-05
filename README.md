# pytidepool

A Python client for the [Tidepool](https://tidepool.org) diabetes data API.

Tidepool is an open-source, nonprofit platform that stores and visualises diabetes device data — continuous glucose monitor (CGM) readings, insulin pump boluses and basal rates, fingerstick values, and more. This library gives you a clean Python interface to that data.

## Installation

```bash
pip install pytidepool
```

```bash
uv add pytidepool
```

## Quick Start

```python
from pytidepool import TidepoolClient, Environment, DiabetesType

with TidepoolClient(
    environment=Environment.PRODUCTION,
    username="user@example.com",
    password="your-password",
) as client:
    readings = client.data.get(
        data_types=[DiabetesType.CBG],
    )
    for r in readings:
        print(r.time, r.value, r.units)
```

`TidepoolClient` is **synchronous** — no `async`/`await` needed. For async usage see [AsyncTidepoolClient](#async-client).

## Common Use Cases

### 1. Fetch CGM glucose readings

```python
from datetime import datetime, timedelta, timezone
from pytidepool import TidepoolClient, Environment, DiabetesType

with TidepoolClient(
    environment=Environment.PRODUCTION,
    username="user@example.com",
    password="your-password",
) as client:
    readings = client.data.get(
        data_types=[DiabetesType.CBG],
        start_date=datetime.now(timezone.utc) - timedelta(days=14),
        end_date=datetime.now(timezone.utc),
    )
    for reading in readings:
        print(f"{reading.time}  {reading.value:.2f} {reading.units}")
```

### 2. Get time-in-range summary (CGM stats)

```python
from pytidepool import TidepoolClient, Environment

with TidepoolClient(
    environment=Environment.PRODUCTION,
    username="user@example.com",
    password="your-password",
) as client:
    summary = client.summary.get_cgm()

    # summary.periods is keyed by period name: "1d", "7d", "14d", "30d"
    period_14d = summary.periods and summary.periods.get("14d")
    if period_14d and period_14d.time_in_range:
        tir = period_14d.time_in_range
        print(f"Time in range (14d): {tir.target_percent:.1f}%")
        print(f"Time below range:    {tir.low_percent:.1f}%")
        print(f"Time above range:    {tir.high_percent:.1f}%")
```

### 3. List clinic patients (clinician / care team use case)

```python
from pytidepool import TidepoolClient, Environment

with TidepoolClient(
    environment=Environment.PRODUCTION,
    client_id="my-app-client-id",
    client_secret="my-app-client-secret",
) as client:
    clinics = client.clinics.list()
    print(f"Found {len(clinics)} clinic(s)")

    patients = client.clinics.get_patients("clinic-id-here")
    for patient in patients:
        print(f"  {patient.full_name}  ({patient.mrn})")
```

### 4. Read a user profile

```python
from pytidepool import TidepoolClient, Environment

with TidepoolClient(
    environment=Environment.PRODUCTION,
    username="user@example.com",
    password="your-password",
) as client:
    profile = client.metadata.get_profile()
    print(f"Name: {profile.full_name}")
    if profile.patient:
        print(f"Birthday: {profile.patient.birthday}")
```

## Authentication

### Username and password (simplest)

```python
with TidepoolClient(
    environment=Environment.PRODUCTION,
    username="user@example.com",
    password="your-password",
) as client:
    ...
```

### Client credentials (server-to-server / clinic apps)

```python
with TidepoolClient(
    environment=Environment.PRODUCTION,
    client_id="your-client-id",
    client_secret="your-client-secret",
) as client:
    ...
```

Tokens are fetched on first use and refreshed automatically. You do not need to manage tokens manually.

### Environments

| Constant | Base URL | Notes |
|---|---|---|
| `Environment.PRODUCTION` | `api.tidepool.org` | Live data |
| `Environment.INTEGRATION` | `int-api.tidepool.org` | For development & testing |
| `Environment.DEV1` | `dev1-api.tidepool.org` | Internal dev |
| `Environment.QA1` … `QA5` | `qa{n}-api.tidepool.org` | QA environments |

Always use `Environment.INTEGRATION` during development.

## Error Handling

```python
from pytidepool import (
    TidepoolClient,
    Environment,
    TidepoolAuthError,
    TidepoolNotFoundError,
    TidepoolRateLimitError,
    TidepoolHTTPError,
)

with TidepoolClient(
    environment=Environment.PRODUCTION,
    username="user@example.com",
    password="your-password",
) as client:
    try:
        readings = client.data.get()
    except TidepoolAuthError:
        print("Authentication failed — check credentials.")
    except TidepoolNotFoundError:
        print("User not found.")
    except TidepoolRateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after}s.")
    except TidepoolHTTPError as e:
        print(f"HTTP error {e.status_code}: {e}")
```

### Exception hierarchy

```
TidepoolError
├── TidepoolConfigurationError   — bad client init (missing credentials)
└── TidepoolHTTPError            — non-2xx API response
    ├── TidepoolAuthError        — 401 / 403
    ├── TidepoolNotFoundError    — 404
    ├── TidepoolRateLimitError   — 429  (.retry_after in seconds)
    └── TidepoolServerError      — 5xx
```

## Async Client

If you are already in an async context, use `AsyncTidepoolClient`:

```python
import asyncio
from pytidepool import AsyncTidepoolClient, Environment, DiabetesType

async def main():
    async with AsyncTidepoolClient(
        environment=Environment.PRODUCTION,
        username="user@example.com",
        password="your-password",
    ) as client:
        readings = await client.data.get(
            data_types=[DiabetesType.CBG],
        )
        for r in readings:
            print(r.time, r.value, r.units)

asyncio.run(main())
```

`AsyncTidepoolClient` exposes exactly the same resource properties (`.data`, `.clinics`, `.summary`, `.metadata`) as `TidepoolClient`, but every method is a coroutine you `await`.

## Data Types

The `DiabetesType` enum maps to Tidepool's data model type strings:

| Enum value | API string | Description |
|---|---|---|
| `DiabetesType.CBG` | `cbg` | CGM sensor glucose reading |
| `DiabetesType.SMBG` | `smbg` | Fingerstick blood glucose |
| `DiabetesType.BOLUS` | `bolus` | Insulin bolus delivery |
| `DiabetesType.BASAL` | `basal` | Basal insulin rate |
| `DiabetesType.DEVICE_EVENT` | `deviceEvent` | Alarms, calibrations, primes, etc. |
| `DiabetesType.PUMP_SETTINGS` | `pumpSettings` | Pump configuration |
| `DiabetesType.WIZARD` | `wizard` | Bolus calculator entry |

Glucose values are returned in **mmol/L** by the Tidepool API. Multiply by 18.0182 to convert to mg/dL.

## API Reference

Full Tidepool API documentation: [tidepool.redocly.app](https://tidepool.redocly.app)

OpenAPI specifications: [github.com/tidepool-org/TidepoolApi](https://github.com/tidepool-org/TidepoolApi)

## License

BSD-2-Clause (same as Tidepool's open-source projects).
