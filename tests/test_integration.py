"""Integration tests against the Tidepool API.

These tests require real credentials — see conftest.py for setup instructions.
Each test targets one resource area and verifies:
  - The request succeeds (no exception)
  - The response parses into the expected Python types
  - Core fields have plausible values (not a full data assertion)

Run with:
    export TIDEPOOL_USERNAME=your@email.com
    export TIDEPOOL_PASSWORD=yourpassword
    pytest tests/test_integration.py -v
"""

from __future__ import annotations

import pytest

from pytidepool import (
    AsyncTidepoolClient,
    TidepoolClient,
    Environment,
    DiabetesType,
    TidepoolAuthError,
    TidepoolConfigurationError,
    CgmSummary,
    BgmSummary,
    UserProfile,
)
from pytidepool.models.clinic import Clinic, Patient, Clinician
from pytidepool.models.data import CbgReading

pytestmark = pytest.mark.integration


# ===========================================================================
# Sync client tests
# ===========================================================================


class TestSyncClient:
    """Smoke tests for TidepoolClient (sync wrapper)."""

    def test_missing_credentials_raise_config_error(self) -> None:
        with pytest.raises(TidepoolConfigurationError):
            TidepoolClient(environment=Environment.INTEGRATION)

    def test_get_profile(self, sync_client: TidepoolClient) -> None:
        profile = sync_client.metadata.get_profile()
        assert isinstance(profile, UserProfile)

    def test_get_collections(self, sync_client: TidepoolClient) -> None:
        collections = sync_client.metadata.get_collections()
        assert isinstance(collections, list)

    def test_get_data(self, sync_client: TidepoolClient) -> None:
        readings = sync_client.data.get()
        assert isinstance(readings, list)

    def test_get_cbg(self, sync_client: TidepoolClient) -> None:
        readings = sync_client.data.get(data_types=[DiabetesType.CBG])
        assert isinstance(readings, list)
        for r in readings:
            assert isinstance(r, CbgReading)

    def test_get_cgm_summary(self, sync_client: TidepoolClient) -> None:
        summary = sync_client.summary.get_cgm()
        assert isinstance(summary, CgmSummary)

    def test_get_bgm_summary(self, sync_client: TidepoolClient) -> None:
        summary = sync_client.summary.get_bgm()
        assert isinstance(summary, BgmSummary)

    def test_list_datasets(self, sync_client: TidepoolClient) -> None:
        datasets = sync_client.data.list_datasets()
        assert isinstance(datasets, list)

    def test_list_clinics(self, sync_client: TidepoolClient) -> None:
        try:
            clinics = sync_client.clinics.list()
            assert isinstance(clinics, list)
        except TidepoolAuthError as e:
            if e.status_code == 403:
                pytest.skip("Account does not have clinic access")
            raise


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


class TestAuth:
    async def test_login_succeeds(self, client: AsyncTidepoolClient) -> None:
        """A valid login yields a non-empty access token."""
        assert client._httpx_client is not None
        token = await client._auth.get_valid_token(client._httpx_client)
        assert isinstance(token, str)
        assert len(token) > 0

    async def test_token_is_cached(self, client: AsyncTidepoolClient) -> None:
        """Calling get_valid_token twice returns the same token (no extra HTTP round-trip)."""
        assert client._httpx_client is not None
        token1 = await client._auth.get_valid_token(client._httpx_client)
        token2 = await client._auth.get_valid_token(client._httpx_client)
        assert token1 == token2

    async def test_bad_credentials_raise_auth_error(self) -> None:
        """Wrong password must raise TidepoolAuthError when the API is reachable."""
        import httpx

        async with AsyncTidepoolClient(
            environment=Environment.INTEGRATION,
            username="nobody@example.invalid",
            password="wrong-password",
        ) as bad_client:
            assert bad_client._httpx_client is not None
            try:
                await bad_client._auth.get_valid_token(bad_client._httpx_client)
                pytest.fail("Expected TidepoolAuthError was not raised")
            except TidepoolAuthError:
                pass  # expected
            except httpx.ConnectError:
                pytest.skip("Cannot reach integration API — no network connectivity")

    def test_missing_credentials_raise_config_error(self) -> None:
        """Constructing a client without any credentials raises TidepoolConfigurationError."""
        with pytest.raises(TidepoolConfigurationError):
            AsyncTidepoolClient(environment=Environment.INTEGRATION)


# ---------------------------------------------------------------------------
# Metadata / user profile
# ---------------------------------------------------------------------------


class TestMetadata:
    async def test_get_collections_returns_list(
        self, client: AsyncTidepoolClient
    ) -> None:
        """The metadata collections endpoint returns a list of strings."""
        collections = await client.metadata.get_collections()
        assert isinstance(collections, list)

    async def test_get_profile_returns_user_profile(
        self, client: AsyncTidepoolClient
    ) -> None:
        """Fetching the profile collection parses into a UserProfile."""
        profile = await client.metadata.get_profile()
        assert isinstance(profile, UserProfile)

    async def test_get_raw_profile_is_dict(
        self, client: AsyncTidepoolClient
    ) -> None:
        """Raw metadata GET returns a plain dict."""
        raw = await client.metadata.get(collection="profile")
        assert isinstance(raw, dict)


# ---------------------------------------------------------------------------
# Diabetes data
# ---------------------------------------------------------------------------


class TestData:
    async def test_get_returns_list(self, client: AsyncTidepoolClient) -> None:
        """data.get() always returns a list, even if no data exists for the account."""
        readings = await client.data.get()
        assert isinstance(readings, list)

    async def test_get_cbg_only(self, client: AsyncTidepoolClient) -> None:
        """Filtering by CBG type only returns CbgReading instances."""
        readings = await client.data.get(data_types=[DiabetesType.CBG])
        assert isinstance(readings, list)
        for r in readings:
            assert isinstance(r, CbgReading), f"Expected CbgReading, got {type(r)}"

    async def test_get_latest_flag(self, client: AsyncTidepoolClient) -> None:
        """latest=True returns at most one record per data type."""
        readings = await client.data.get(latest=True)
        assert isinstance(readings, list)
        seen_types: set[str] = set()
        for r in readings:
            assert r.type not in seen_types, (
                f"latest=True returned duplicate type '{r.type}'"
            )
            seen_types.add(r.type)

    async def test_get_multiple_types(self, client: AsyncTidepoolClient) -> None:
        """Requesting multiple types returns only those types."""
        requested = [DiabetesType.CBG, DiabetesType.SMBG, DiabetesType.BOLUS]
        readings = await client.data.get(data_types=requested)
        allowed_types = {dt.value for dt in requested}
        for r in readings:
            assert r.type in allowed_types, (
                f"Got unexpected type '{r.type}' when requesting {allowed_types}"
            )

    async def test_list_datasets_returns_list(
        self, client: AsyncTidepoolClient
    ) -> None:
        """list_datasets() returns a list (may be empty for a fresh dev account)."""
        datasets = await client.data.list_datasets()
        assert isinstance(datasets, list)

    async def test_cbg_reading_fields(self, client: AsyncTidepoolClient) -> None:
        """Any returned CBG readings have valid value and time fields."""
        readings = await client.data.get(
            data_types=[DiabetesType.CBG], latest=True
        )
        for r in readings:
            assert isinstance(r, CbgReading)
            assert r.value > 0, "CBG value must be positive"
            assert r.time is not None


# ---------------------------------------------------------------------------
# CGM / BGM summary
# ---------------------------------------------------------------------------


class TestSummary:
    async def test_get_cgm_summary(self, client: AsyncTidepoolClient) -> None:
        """get_cgm() returns a CgmSummary regardless of whether data exists."""
        summary = await client.summary.get_cgm()
        assert isinstance(summary, CgmSummary)

    async def test_get_bgm_summary(self, client: AsyncTidepoolClient) -> None:
        """get_bgm() returns a BgmSummary."""
        summary = await client.summary.get_bgm()
        assert isinstance(summary, BgmSummary)

    async def test_cgm_summary_periods_structure(
        self, client: AsyncTidepoolClient
    ) -> None:
        """If the CGM summary has period data, time-in-range values are floats."""
        summary = await client.summary.get_cgm()
        if not summary.periods:
            pytest.skip("No summary period data for this account")
        for period_name, period in summary.periods.items():
            tir = period.time_in_range
            if tir is None:
                continue
            for attr in ("target_percent", "low_percent", "high_percent"):
                value = getattr(tir, attr)
                if value is not None:
                    assert isinstance(value, float), (
                        f"{period_name}.time_in_range.{attr} should be float, got {type(value)}"
                    )


# ---------------------------------------------------------------------------
# Clinics
# ---------------------------------------------------------------------------


class TestClinics:
    async def test_list_clinics_returns_list(self, client: AsyncTidepoolClient) -> None:
        """list() returns a list — may be empty for a personal account, or 403 for non-clinicians."""
        try:
            clinics = await client.clinics.list()
            assert isinstance(clinics, list)
        except TidepoolAuthError as e:
            if e.status_code == 403:
                pytest.skip("Account does not have clinic (clinician) access")
            raise

    async def test_clinic_objects_are_typed(self, client: AsyncTidepoolClient) -> None:
        """Every item in the clinic list is a Clinic instance."""
        try:
            clinics = await client.clinics.list()
        except TidepoolAuthError as e:
            if e.status_code == 403:
                pytest.skip("Account does not have clinic (clinician) access")
            raise
        for clinic in clinics:
            assert isinstance(clinic, Clinic)

    async def test_get_patients_for_each_clinic(
        self, client: AsyncTidepoolClient
    ) -> None:
        """For each accessible clinic, get_patients() returns a list of Patient objects."""
        try:
            clinics = await client.clinics.list()
        except TidepoolAuthError as e:
            if e.status_code == 403:
                pytest.skip("Account does not have clinic (clinician) access")
            raise
        if not clinics:
            pytest.skip("No clinics accessible for this account")
        for clinic in clinics:
            assert clinic.id is not None
            patients = await client.clinics.get_patients(clinic.id)
            assert isinstance(patients, list)
            for patient in patients:
                assert isinstance(patient, Patient)

    async def test_list_clinicians(self, client: AsyncTidepoolClient) -> None:
        """For each accessible clinic, list_clinicians() returns a list of Clinician objects."""
        try:
            clinics = await client.clinics.list()
        except TidepoolAuthError as e:
            if e.status_code == 403:
                pytest.skip("Account does not have clinic (clinician) access")
            raise
        if not clinics:
            pytest.skip("No clinics accessible for this account")
        for clinic in clinics:
            assert clinic.id is not None
            clinicians = await client.clinics.list_clinicians(clinic.id)
            assert isinstance(clinicians, list)
            for clinician in clinicians:
                assert isinstance(clinician, Clinician)
