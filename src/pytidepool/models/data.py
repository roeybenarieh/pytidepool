from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _DiabetesBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    time: datetime
    device_id: str | None = Field(None, alias="deviceId")
    upload_id: str | None = Field(None, alias="uploadId")
    timezone: str | None = None
    units: str | None = None


class CbgReading(_DiabetesBase):
    """Continuous Blood Glucose reading (CGM sensor data)."""

    type: Literal["cbg"]
    value: float


class SmbgReading(_DiabetesBase):
    """Self-Monitored Blood Glucose reading (fingerstick)."""

    type: Literal["smbg"]
    value: float
    sub_type: str | None = Field(None, alias="subType")


class Bolus(_DiabetesBase):
    """Insulin bolus delivery."""

    type: Literal["bolus"]
    sub_type: str | None = Field(None, alias="subType")
    normal: float | None = None
    extended: float | None = None
    duration: int | None = None  # milliseconds
    expected_normal: float | None = Field(None, alias="expectedNormal")
    expected_extended: float | None = Field(None, alias="expectedExtended")
    expected_duration: int | None = Field(None, alias="expectedDuration")


class BasalRate(_DiabetesBase):
    """Basal insulin rate."""

    type: Literal["basal"]
    delivery_type: str | None = Field(None, alias="deliveryType")
    rate: float | None = None
    duration: int | None = None  # milliseconds
    expected_duration: int | None = Field(None, alias="expectedDuration")
    schedule_name: str | None = Field(None, alias="scheduleName")


class DeviceEvent(_DiabetesBase):
    """Device events (alarms, calibrations, prime, reservoirChange, status, timeChange)."""

    type: Literal["deviceEvent"]
    sub_type: str | None = Field(None, alias="subType")
    alarm_type: str | None = Field(None, alias="alarmType")
    status: str | None = None
    duration: int | None = None


class PumpSettings(_DiabetesBase):
    """Insulin pump configuration settings."""

    type: Literal["pumpSettings"]
    # The API returns units as a dict e.g. {"bg": "mg/dL", "carb": "grams"},
    # overriding the str | None definition on the base class.
    units: dict[str, str] | str | None = None
    active_schedule: str | None = Field(None, alias="activeSchedule")
    basal_schedules: dict[str, Any] | None = Field(None, alias="basalSchedules")
    bg_target: Any | None = Field(None, alias="bgTarget")
    carb_ratio: Any | None = Field(None, alias="carbRatio")
    insulin_sensitivity: Any | None = Field(None, alias="insulinSensitivity")


class Wizard(_DiabetesBase):
    """Bolus wizard / insulin dose calculator entry."""

    type: Literal["wizard"]
    bolus: str | None = None
    carb_input: float | None = Field(None, alias="carbInput")
    bg_input: float | None = Field(None, alias="bgInput")
    recommended: dict[str, Any] | None = None


DiabetesReading = Annotated[
    CbgReading | SmbgReading | Bolus | BasalRate | DeviceEvent | PumpSettings | Wizard,
    Field(discriminator="type"),
]
