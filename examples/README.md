# pytidepool Examples

Each subdirectory is a standalone example. All examples use the synchronous `TidepoolClient` — no `async`/`await` needed.

## Examples

| Directory | Description |
|---|---|
| [`fetch_cgm_readings/`](fetch_cgm_readings/) | Fetch CGM readings for a date range and print them |
| [`time_in_range_summary/`](time_in_range_summary/) | Print CGM/BGM time-in-range stats across 1d/7d/14d/30d windows |
| [`read_user_profile/`](read_user_profile/) | Read a user's profile and available metadata collections |
| [`list_clinic_patients/`](list_clinic_patients/) | List patients across all clinics (clinician/client-credentials flow) |
| [`visualize_cgm/`](visualize_cgm/) | Plot CGM readings as a color-coded time-series chart |

## Quick start

All personal-account examples share the same three env vars:

```bash
export TIDEPOOL_USERNAME=your@email.com
export TIDEPOOL_PASSWORD=yourpassword
export TIDEPOOL_USER_ID=your-user-id
```

Then run any example directly:

```bash
python fetch_cgm_readings/fetch_cgm_readings.py
python visualize_cgm/visualize_cgm.py
```

The clinic example uses client credentials instead:

```bash
export TIDEPOOL_CLIENT_ID=your-client-id
export TIDEPOOL_CLIENT_SECRET=your-client-secret
python list_clinic_patients/list_clinic_patients.py
```
