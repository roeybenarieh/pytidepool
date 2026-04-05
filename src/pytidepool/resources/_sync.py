from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Coroutine

from pytidepool._enums import DiabetesType, SummaryType
from pytidepool.models.clinic import Clinic, Clinician, Patient
from pytidepool.models.data import DiabetesReading
from pytidepool.models.metadata import UserProfile
from pytidepool.models.summary import BgmSummary, CgmSummary
from pytidepool.resources.clinics import ClinicsResource
from pytidepool.resources.data import DataResource, Dataset, UploadResponse
from pytidepool.resources.metadata import MetadataResource
from pytidepool.resources.summary import SummaryResource

_RunFn = Callable[[Coroutine[Any, Any, Any]], Any]


class SyncDataResource:
    """Synchronous wrapper around :class:`DataResource`."""

    def __init__(self, resource: DataResource, run_fn: _RunFn) -> None:
        self._resource = resource
        self._run = run_fn

    def get(
        self,
        user_id: str,
        *,
        data_types: list[DiabetesType] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        device_id: str | None = None,
        latest: bool = False,
    ) -> list[DiabetesReading]:
        return self._run(  # type: ignore[return-value]
            self._resource.get(
                user_id,
                data_types=data_types,
                start_date=start_date,
                end_date=end_date,
                device_id=device_id,
                latest=latest,
            )
        )

    def list_datasets(self, user_id: str) -> list[Dataset]:
        return self._run(self._resource.list_datasets(user_id))  # type: ignore[return-value]

    def delete_dataset(self, dataset_id: str) -> None:
        self._run(self._resource.delete_dataset(dataset_id))

    def upload(
        self,
        user_id: str,
        readings: list[DiabetesReading],
        *,
        dataset_id: str | None = None,
    ) -> UploadResponse:
        return self._run(  # type: ignore[return-value]
            self._resource.upload(user_id, readings, dataset_id=dataset_id)
        )


class SyncClinicsResource:
    """Synchronous wrapper around :class:`ClinicsResource`."""

    def __init__(self, resource: ClinicsResource, run_fn: _RunFn) -> None:
        self._resource = resource
        self._run = run_fn

    def list(self, *, limit: int = 100, offset: int = 0) -> list[Clinic]:
        return self._run(self._resource.list(limit=limit, offset=offset))  # type: ignore[return-value]

    def get(self, clinic_id: str) -> Clinic:
        return self._run(self._resource.get(clinic_id))  # type: ignore[return-value]

    def get_patients(
        self,
        clinic_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
    ) -> list[Patient]:
        return self._run(  # type: ignore[return-value]
            self._resource.get_patients(
                clinic_id, limit=limit, offset=offset, search=search
            )
        )

    def get_patient(self, clinic_id: str, patient_id: str) -> Patient:
        return self._run(self._resource.get_patient(clinic_id, patient_id))  # type: ignore[return-value]

    def list_clinicians(
        self,
        clinic_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Clinician]:
        return self._run(  # type: ignore[return-value]
            self._resource.list_clinicians(clinic_id, limit=limit, offset=offset)
        )


class SyncSummaryResource:
    """Synchronous wrapper around :class:`SummaryResource`."""

    def __init__(self, resource: SummaryResource, run_fn: _RunFn) -> None:
        self._resource = resource
        self._run = run_fn

    def get_cgm(self, user_id: str) -> CgmSummary:
        return self._run(self._resource.get_cgm(user_id))  # type: ignore[return-value]

    def get_bgm(self, user_id: str) -> BgmSummary:
        return self._run(self._resource.get_bgm(user_id))  # type: ignore[return-value]

    def get(self, user_id: str, summary_type: SummaryType) -> CgmSummary | BgmSummary:
        return self._run(self._resource.get(user_id, summary_type))  # type: ignore[return-value]


class SyncMetadataResource:
    """Synchronous wrapper around :class:`MetadataResource`."""

    def __init__(self, resource: MetadataResource, run_fn: _RunFn) -> None:
        self._resource = resource
        self._run = run_fn

    def get(self, user_id: str, collection: str) -> dict[str, Any]:
        return self._run(self._resource.get(user_id, collection))  # type: ignore[return-value]

    def get_profile(self, user_id: str) -> UserProfile:
        return self._run(self._resource.get_profile(user_id))  # type: ignore[return-value]

    def update(self, user_id: str, collection: str, data: dict[str, Any]) -> None:
        self._run(self._resource.update(user_id, collection, data))

    def get_collections(self) -> list[str]:
        return self._run(self._resource.get_collections())  # type: ignore[return-value]
