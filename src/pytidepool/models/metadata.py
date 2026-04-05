from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PatientInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    birthday: str | None = None
    diagnosis_date: str | None = Field(None, alias="diagnosisDate")
    diagnosis_type: str | None = Field(None, alias="diagnosisType")
    target_glucose: float | None = Field(None, alias="targetGlucose")
    target_upper_bound: float | None = Field(None, alias="targetUpperBound")
    target_lower_bound: float | None = Field(None, alias="targetLowerBound")
    about: str | None = None


class UserProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    full_name: str | None = Field(None, alias="fullName")
    patient: PatientInfo | None = None
