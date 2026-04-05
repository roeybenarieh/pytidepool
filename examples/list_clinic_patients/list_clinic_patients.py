"""List all patients across all accessible clinics.

Requires a clinician account with clinic access.
Uses client credentials (OAuth2 client_credentials grant).

Usage:
    export TIDEPOOL_CLIENT_ID=your-client-id
    export TIDEPOOL_CLIENT_SECRET=your-client-secret
    python examples/list_clinic_patients.py
"""

import os

from pytidepool import TidepoolClient, Environment, TidepoolAuthError

CLIENT_ID = os.environ["TIDEPOOL_CLIENT_ID"]
CLIENT_SECRET = os.environ["TIDEPOOL_CLIENT_SECRET"]

with TidepoolClient(
    environment=Environment.PRODUCTION,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
) as client:
    try:
        clinics = client.clinics.list()
    except TidepoolAuthError as e:
        if e.status_code == 403:
            print("This account does not have clinic (clinician) access.")
        raise

print(f"Found {len(clinics)} clinic(s).\n")

for clinic in clinics:
    print(f"Clinic: {clinic.name}  (id={clinic.id})")
    patients = client.clinics.get_patients(clinic.id)
    print(f"  {len(patients)} patient(s):")
    for patient in patients:
        name = patient.full_name or "(no name)"
        mrn = f"  MRN={patient.mrn}" if patient.mrn else ""
        print(f"    {name}{mrn}")
    print()
