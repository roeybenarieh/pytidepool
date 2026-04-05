"""pytidepool — Python client for the Tidepool diabetes data API."""

from pytidepool._client import AsyncTidepoolClient
from pytidepool._sync_client import TidepoolClient
from pytidepool.resources._sync import (
    SyncClinicsResource,
    SyncDataResource,
    SyncMetadataResource,
    SyncSummaryResource,
)
from pytidepool._enums import DiabetesType, Environment, SummaryType
from pytidepool._exceptions import (
    TidepoolAuthError,
    TidepoolConfigurationError,
    TidepoolError,
    TidepoolHTTPError,
    TidepoolNotFoundError,
    TidepoolRateLimitError,
    TidepoolServerError,
)
from pytidepool.models import (
    BasalRate,
    BgmSummary,
    Bolus,
    CbgReading,
    CgmSummary,
    Clinic,
    Clinician,
    DeviceEvent,
    DiabetesReading,
    Patient,
    PatientInfo,
    PatientPermissions,
    PumpSettings,
    SmbgReading,
    SummaryPeriod,
    TimeInRange,
    TokenResponse,
    UserProfile,
    Wizard,
)

__all__ = [
    # Clients
    "TidepoolClient",
    "AsyncTidepoolClient",
    # Sync resource types
    "SyncDataResource",
    "SyncClinicsResource",
    "SyncSummaryResource",
    "SyncMetadataResource",
    # Enums
    "Environment",
    "DiabetesType",
    "SummaryType",
    # Exceptions
    "TidepoolError",
    "TidepoolHTTPError",
    "TidepoolAuthError",
    "TidepoolNotFoundError",
    "TidepoolRateLimitError",
    "TidepoolServerError",
    "TidepoolConfigurationError",
    # Models — auth
    "TokenResponse",
    # Models — data
    "DiabetesReading",
    "CbgReading",
    "SmbgReading",
    "Bolus",
    "BasalRate",
    "DeviceEvent",
    "PumpSettings",
    "Wizard",
    # Models — clinic
    "Clinic",
    "Patient",
    "Clinician",
    "PatientPermissions",
    # Models — summary
    "CgmSummary",
    "BgmSummary",
    "SummaryPeriod",
    "TimeInRange",
    # Models — metadata
    "UserProfile",
    "PatientInfo",
]
