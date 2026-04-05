from __future__ import annotations

from typing import Any

from pytidepool.models.clinic import Clinic, Clinician, Patient
from pytidepool.resources._base import AsyncResource


class ClinicsResource(AsyncResource):
    """Manage clinics, patients, and clinicians."""

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Clinic]:
        """List all clinics accessible to the authenticated user."""
        response = await self._http.get(
            "/v1/clinics", params={"limit": limit, "offset": offset}
        )
        body: Any = response.json()
        items: list[dict[str, Any]] = (
            body if isinstance(body, list) else body.get("data", [])
        )
        return [Clinic.model_validate(item) for item in items]

    async def get(self, clinic_id: str) -> Clinic:
        """Get a clinic by ID."""
        response = await self._http.get(f"/v1/clinics/{clinic_id}")
        return Clinic.model_validate(response.json())

    async def get_patients(
        self,
        clinic_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
    ) -> list[Patient]:
        """List all patients in a clinic."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        response = await self._http.get(
            f"/v1/clinics/{clinic_id}/patients", params=params
        )
        body: Any = response.json()
        items: list[dict[str, Any]] = (
            body if isinstance(body, list) else body.get("data", [])
        )
        return [Patient.model_validate(item) for item in items]

    async def get_patient(self, clinic_id: str, patient_id: str) -> Patient:
        """Get a single patient from a clinic."""
        response = await self._http.get(
            f"/v1/clinics/{clinic_id}/patients/{patient_id}"
        )
        return Patient.model_validate(response.json())

    async def list_clinicians(
        self,
        clinic_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Clinician]:
        """List all clinicians in a clinic."""
        response = await self._http.get(
            f"/v1/clinics/{clinic_id}/clinicians",
            params={"limit": limit, "offset": offset},
        )
        body: Any = response.json()
        items: list[dict[str, Any]] = (
            body if isinstance(body, list) else body.get("data", [])
        )
        return [Clinician.model_validate(item) for item in items]
