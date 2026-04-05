from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Clinic(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str | None = Field(None, alias="id")
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    phone_numbers: list[dict] | None = Field(None, alias="phoneNumbers")
    email: str | None = None
    tier: str | None = None
    share_code: str | None = Field(None, alias="shareCode")
    created_time: str | None = Field(None, alias="createdTime")
    updated_time: str | None = Field(None, alias="updatedTime")


class PatientPermissions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    custodian: dict | None = None
    view: dict | None = None
    upload: dict | None = None
    note: dict | None = None


class Patient(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str | None = Field(None, alias="id")
    email: str | None = None
    full_name: str | None = Field(None, alias="fullName")
    birth_date: str | None = Field(None, alias="birthDate")
    mrn: str | None = None
    permissions: PatientPermissions | None = None
    tags: list[str] | None = None
    reviews: list[dict] | None = None
    created_time: str | None = Field(None, alias="createdTime")
    updated_time: str | None = Field(None, alias="updatedTime")


class Clinician(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str | None = Field(None, alias="id")
    user_id: str | None = Field(None, alias="userId")
    email: str | None = None
    name: str | None = None
    roles: list[str] | None = None
    invite_id: str | None = Field(None, alias="inviteId")
    created_time: str | None = Field(None, alias="createdTime")
    updated_time: str | None = Field(None, alias="updatedTime")
