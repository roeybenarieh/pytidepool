from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TimeInRange(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    very_low_minutes: int | None = Field(None, alias="veryLowMinutes")
    very_low_records: int | None = Field(None, alias="veryLowRecords")
    very_low_percent: float | None = Field(None, alias="veryLowPercent")

    low_minutes: int | None = Field(None, alias="lowMinutes")
    low_records: int | None = Field(None, alias="lowRecords")
    low_percent: float | None = Field(None, alias="lowPercent")

    target_minutes: int | None = Field(None, alias="targetMinutes")
    target_records: int | None = Field(None, alias="targetRecords")
    target_percent: float | None = Field(None, alias="targetPercent")

    high_minutes: int | None = Field(None, alias="highMinutes")
    high_records: int | None = Field(None, alias="highRecords")
    high_percent: float | None = Field(None, alias="highPercent")

    very_high_minutes: int | None = Field(None, alias="veryHighMinutes")
    very_high_records: int | None = Field(None, alias="veryHighRecords")
    very_high_percent: float | None = Field(None, alias="veryHighPercent")


class GlucoseStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    average_glucose_mmol: float | None = Field(None, alias="averageGlucoseMmol")
    gmi_percent: float | None = Field(None, alias="gmiPercent")
    cv: float | None = None
    time_in_range: TimeInRange | None = Field(None, alias="timeInRange")
    total_records: int | None = Field(None, alias="totalRecords")


class SummaryPeriod(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    has_sufficient_data: bool | None = Field(None, alias="hasSufficientData")
    average_glucose_mmol: float | None = Field(None, alias="averageGlucoseMmol")
    gmi_percent: float | None = Field(None, alias="gmiPercent")
    cv: float | None = None
    time_in_range: TimeInRange | None = Field(None, alias="timeInRange")
    total_records: int | None = Field(None, alias="totalRecords")
    time_in_auto_ratio: float | None = Field(None, alias="timeInAutoRatio")


class CgmSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    user_id: str | None = Field(None, alias="userId")
    type: str | None = None
    last_upload_date: datetime | None = Field(None, alias="lastUploadDate")
    first_data: datetime | None = Field(None, alias="firstData")
    last_data: datetime | None = Field(None, alias="lastData")
    outdated_since: datetime | None = Field(None, alias="outdatedSince")
    periods: dict[str, SummaryPeriod] | None = None
    config: dict | None = None


class BgmSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    user_id: str | None = Field(None, alias="userId")
    type: str | None = None
    last_upload_date: datetime | None = Field(None, alias="lastUploadDate")
    first_data: datetime | None = Field(None, alias="firstData")
    last_data: datetime | None = Field(None, alias="lastData")
    outdated_since: datetime | None = Field(None, alias="outdatedSince")
    periods: dict[str, SummaryPeriod] | None = None
    config: dict | None = None
