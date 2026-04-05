"""Unit tests for Pydantic data models."""

from __future__ import annotations

import time

from pytidepool.models.auth import TokenResponse
from pytidepool.models.data import (
    CbgReading,
    SmbgReading,
    Bolus,
    BasalRate,
    DiabetesReading,
)
from pytidepool.models.metadata import UserProfile
from pytidepool.models.summary import CgmSummary, BgmSummary
from pytidepool.resources.data import _parse_reading


# ---------------------------------------------------------------------------
# TokenResponse
# ---------------------------------------------------------------------------


class TestTokenResponse:
    def test_fresh_token_not_expired(self) -> None:
        token = TokenResponse(access_token="tok", expires_in=3600)
        assert not token.is_expired()

    def test_expired_token(self) -> None:
        token = TokenResponse(access_token="tok", expires_in=0)
        assert token.is_expired()

    def test_expiry_buffer(self) -> None:
        # expires_in=60 but buffer=90 → should report as expired
        token = TokenResponse(access_token="tok", expires_in=60)
        assert token.is_expired(buffer_seconds=90)

    def test_no_refresh_token_is_expired(self) -> None:
        token = TokenResponse(access_token="tok", expires_in=3600)
        assert token.refresh_token_is_expired()

    def test_fresh_refresh_token_not_expired(self) -> None:
        token = TokenResponse(
            access_token="tok",
            expires_in=3600,
            refresh_token="ref",
            refresh_expires_in=7200,
        )
        assert not token.refresh_token_is_expired()


# ---------------------------------------------------------------------------
# Diabetes data models
# ---------------------------------------------------------------------------

_CBG_RAW = {
    "type": "cbg",
    "id": "abc123",
    "time": "2024-06-01T12:00:00Z",
    "uploadId": "upload-1",
    "value": 5.5,
    "units": "mmol/L",
}

_SMBG_RAW = {
    "type": "smbg",
    "id": "smbg-1",
    "time": "2024-06-01T08:00:00Z",
    "uploadId": "upload-1",
    "value": 6.1,
    "units": "mmol/L",
}

_BOLUS_RAW = {
    "type": "bolus",
    "id": "bolus-1",
    "time": "2024-06-01T12:30:00Z",
    "uploadId": "upload-1",
    "subType": "normal",
    "normal": 2.5,
}


class TestCbgReading:
    def test_parses_from_camel_case(self) -> None:
        reading = CbgReading.model_validate(_CBG_RAW)
        assert reading.type == "cbg"
        assert reading.value == 5.5
        assert reading.upload_id == "upload-1"

    def test_parse_reading_returns_cbg(self) -> None:
        result = _parse_reading(_CBG_RAW)
        assert isinstance(result, CbgReading)

    def test_parse_reading_returns_smbg(self) -> None:
        result = _parse_reading(_SMBG_RAW)
        assert isinstance(result, SmbgReading)

    def test_parse_reading_returns_bolus(self) -> None:
        result = _parse_reading(_BOLUS_RAW)
        assert isinstance(result, Bolus)

    def test_parse_reading_unknown_type_returns_none(self) -> None:
        result = _parse_reading({"type": "unknownFutureType", "id": "x"})
        assert result is None

    def test_parse_reading_missing_type_returns_none(self) -> None:
        result = _parse_reading({"id": "x", "value": 5.0})
        assert result is None

    def test_extra_fields_accepted(self) -> None:
        raw = {**_CBG_RAW, "futureField": "some value"}
        reading = CbgReading.model_validate(raw)
        assert reading.type == "cbg"


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------


class TestUserProfile:
    def test_minimal_profile(self) -> None:
        profile = UserProfile.model_validate({"fullName": "Test User"})
        assert profile.full_name == "Test User"
        assert profile.patient is None

    def test_profile_with_patient(self) -> None:
        raw = {
            "fullName": "Test User",
            "patient": {"birthday": "1990-01-01", "diagnosisType": "type1"},
        }
        profile = UserProfile.model_validate(raw)
        assert profile.patient is not None
        assert profile.patient.birthday == "1990-01-01"
        assert profile.patient.diagnosis_type == "type1"

    def test_empty_profile_is_valid(self) -> None:
        profile = UserProfile.model_validate({})
        assert profile.full_name is None
        assert profile.patient is None


# ---------------------------------------------------------------------------
# Summary models
# ---------------------------------------------------------------------------


class TestSummaryModels:
    def test_cgm_summary_minimal(self) -> None:
        summary = CgmSummary.model_validate({})
        assert summary.periods is None

    def test_bgm_summary_minimal(self) -> None:
        summary = BgmSummary.model_validate({})
        assert summary.periods is None

    def test_cgm_summary_with_periods(self) -> None:
        raw = {
            "periods": {
                "7d": {
                    "timeInRange": {
                        "targetPercent": 0.72,
                        "lowPercent": 0.05,
                        "highPercent": 0.23,
                    }
                }
            }
        }
        summary = CgmSummary.model_validate(raw)
        assert summary.periods is not None
        period = summary.periods["7d"]
        assert period.time_in_range is not None
        assert period.time_in_range.target_percent == 0.72
