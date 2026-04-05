from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import TypeAdapter

from pytidepool._enums import DiabetesType
from pytidepool.models.data import (
    BasalRate,
    Bolus,
    CbgReading,
    DeviceEvent,
    DiabetesReading,
    PumpSettings,
    SmbgReading,
    Wizard,
)
from pytidepool.resources._base import AsyncResource

_READING_ADAPTER: TypeAdapter[DiabetesReading] = TypeAdapter(DiabetesReading)

_KNOWN_TYPES = {
    "cbg": CbgReading,
    "smbg": SmbgReading,
    "bolus": Bolus,
    "basal": BasalRate,
    "deviceEvent": DeviceEvent,
    "pumpSettings": PumpSettings,
    "wizard": Wizard,
}


def _parse_reading(raw: dict[str, Any]) -> DiabetesReading | None:
    dtype = raw.get("type", "")
    if dtype not in _KNOWN_TYPES:
        return None
    return _READING_ADAPTER.validate_python(raw)


class Dataset:
    """Minimal representation of a Tidepool dataset."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.id: str | None = data.get("id") or data.get("uploadId")
        self.device_id: str | None = data.get("deviceId")
        self.type: str | None = data.get("type")
        self.created_time: str | None = data.get("createdTime")
        self._raw = data


class UploadResponse:
    def __init__(self, data: dict[str, Any]) -> None:
        self._raw = data


class DataResource(AsyncResource):
    """Access and upload diabetes device data."""

    async def get(
        self,
        user_id: str,
        *,
        data_types: list[DiabetesType] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        device_id: str | None = None,
        latest: bool = False,
    ) -> list[DiabetesReading]:
        """Fetch diabetes data for a user.

        Args:
            user_id: Tidepool user ID.
            data_types: Filter by one or more diabetes data types.
            start_date: Return data on or after this datetime (UTC).
            end_date: Return data on or before this datetime (UTC).
            device_id: Filter by a specific device ID.
            latest: If True, return only the most recent entry per type.

        Returns:
            List of parsed diabetes readings.
        """
        params: dict[str, Any] = {}
        if data_types:
            params["type"] = ",".join(t.value for t in data_types)
        if start_date:
            params["startDate"] = start_date.isoformat()
        if end_date:
            params["endDate"] = end_date.isoformat()
        if device_id:
            params["deviceId"] = device_id
        if latest:
            params["latest"] = "true"

        response = await self._http.get(f"/data/{user_id}", params=params)
        raw_list: list[dict[str, Any]] = response.json()
        results: list[DiabetesReading] = []
        for item in raw_list:
            parsed = _parse_reading(item)
            if parsed is not None:
                results.append(parsed)
        return results

    async def list_datasets(self, user_id: str) -> list[Dataset]:
        """List all datasets for a user."""
        response = await self._http.get(f"/v1/users/{user_id}/datasets")
        body = response.json()
        # API returns {"data": [...]} or a plain list
        items: list[dict[str, Any]] = (
            body.get("data", body) if isinstance(body, dict) else body
        )
        return [Dataset(item) for item in items]

    async def delete_dataset(self, dataset_id: str) -> None:
        """Delete a dataset by ID."""
        await self._http.delete(f"/v1/datasets/{dataset_id}")

    async def upload(
        self,
        user_id: str,
        readings: list[DiabetesReading],
        *,
        dataset_id: str | None = None,
    ) -> UploadResponse:
        """Upload diabetes data for a user.

        If dataset_id is provided, data is appended to that dataset.
        Otherwise the legacy /data/{userId} endpoint is used.
        """
        payload = [r.model_dump(by_alias=True, exclude_none=True) for r in readings]
        if dataset_id:
            response = await self._http.post(
                f"/v1/datasets/{dataset_id}/data", json=payload
            )
        else:
            response = await self._http.post(f"/data/{user_id}", json=payload)
        body = response.json() if response.content else {}
        return UploadResponse(body if isinstance(body, dict) else {})
