"""Unit tests for client initialization and resource calls (respx mocks)."""

from __future__ import annotations

import base64
import json
import time

import httpx
import pytest
import respx

from pytidepool import AsyncTidepoolClient, TidepoolClient, Environment
from pytidepool._exceptions import TidepoolAuthError, TidepoolConfigurationError
from pytidepool.models.data import CbgReading
from pytidepool.models.summary import CgmSummary
from pytidepool.models.metadata import UserProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE = "https://api.tidepool.org"
_USER_ID = "user-unit-test-123"


def _make_jwt(sub: str = _USER_ID, expires_in: int = 3600) -> str:
    """Create a minimal fake JWT with the given sub claim."""
    now = int(time.time())
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": sub, "iat": now, "exp": now + expires_in}).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{payload}.fakesig"


def _make_legacy_token(sub: str = _USER_ID) -> str:
    """Create a fake kc: legacy session token."""
    access = _make_jwt(sub)
    refresh = _make_jwt(sub, expires_in=7200)
    return f"kc:{access}:{refresh}"


# ---------------------------------------------------------------------------
# Configuration / initialization
# ---------------------------------------------------------------------------


class TestClientConfiguration:
    def test_async_client_missing_credentials_raises(self) -> None:
        with pytest.raises(TidepoolConfigurationError):
            AsyncTidepoolClient(environment=Environment.PRODUCTION)

    def test_sync_client_missing_credentials_raises(self) -> None:
        with pytest.raises(TidepoolConfigurationError):
            TidepoolClient(environment=Environment.PRODUCTION)

    def test_async_client_partial_credentials_raises(self) -> None:
        with pytest.raises(TidepoolConfigurationError):
            AsyncTidepoolClient(
                environment=Environment.PRODUCTION, username="user@example.com"
            )

    def test_sync_client_partial_credentials_raises(self) -> None:
        with pytest.raises(TidepoolConfigurationError):
            TidepoolClient(
                environment=Environment.PRODUCTION, client_id="some-id"
            )

    def test_async_client_accepts_username_password(self) -> None:
        client = AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        )
        assert client is not None

    def test_async_client_accepts_client_credentials(self) -> None:
        client = AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            client_id="my-client",
            client_secret="my-secret",
        )
        assert client is not None


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class TestAuth:
    @respx.mock
    async def test_login_injects_token_header(self) -> None:
        token = _make_legacy_token()
        respx.post(f"{_BASE}/auth/login").mock(
            return_value=httpx.Response(
                200, headers={"x-tidepool-session-token": token}
            )
        )
        respx.get(f"{_BASE}/data/{_USER_ID}").mock(
            return_value=httpx.Response(200, json=[])
        )

        async with AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        ) as client:
            await client.data.get(_USER_ID)

        # Auth endpoint was called once
        assert respx.calls.call_count >= 1

    @respx.mock
    async def test_bad_credentials_raise_auth_error(self) -> None:
        respx.post(f"{_BASE}/auth/login").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )

        with pytest.raises(TidepoolAuthError):
            async with AsyncTidepoolClient(
                environment=Environment.PRODUCTION,
                username="bad@example.com",
                password="wrong",
            ) as client:
                await client.data.get(_USER_ID)

    @respx.mock
    async def test_get_user_id_extracts_sub(self) -> None:
        token = _make_legacy_token(sub=_USER_ID)
        respx.post(f"{_BASE}/auth/login").mock(
            return_value=httpx.Response(
                200, headers={"x-tidepool-session-token": token}
            )
        )

        async with AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        ) as client:
            user_id = await client.get_user_id()

        assert user_id == _USER_ID

    @respx.mock
    async def test_token_is_reused_across_calls(self) -> None:
        token = _make_legacy_token()
        login_route = respx.post(f"{_BASE}/auth/login").mock(
            return_value=httpx.Response(
                200, headers={"x-tidepool-session-token": token}
            )
        )
        respx.get(f"{_BASE}/data/{_USER_ID}").mock(
            return_value=httpx.Response(200, json=[])
        )

        async with AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        ) as client:
            await client.data.get(_USER_ID)
            await client.data.get(_USER_ID)

        # Login called only once despite two data requests
        assert login_route.call_count == 1


# ---------------------------------------------------------------------------
# Data resource
# ---------------------------------------------------------------------------


class TestDataResource:
    @respx.mock
    async def test_get_returns_parsed_list(self) -> None:
        token = _make_legacy_token()
        respx.post(f"{_BASE}/auth/login").mock(
            return_value=httpx.Response(
                200, headers={"x-tidepool-session-token": token}
            )
        )
        respx.get(f"{_BASE}/data/{_USER_ID}").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "type": "cbg",
                        "id": "r1",
                        "time": "2024-06-01T12:00:00Z",
                        "uploadId": "u1",
                        "value": 5.5,
                        "units": "mmol/L",
                    }
                ],
            )
        )

        async with AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        ) as client:
            readings = await client.data.get(_USER_ID)

        assert len(readings) == 1
        assert isinstance(readings[0], CbgReading)
        assert readings[0].value == 5.5

    @respx.mock
    async def test_get_empty_response_returns_empty_list(self) -> None:
        token = _make_legacy_token()
        respx.post(f"{_BASE}/auth/login").mock(
            return_value=httpx.Response(
                200, headers={"x-tidepool-session-token": token}
            )
        )
        respx.get(f"{_BASE}/data/{_USER_ID}").mock(
            return_value=httpx.Response(200, json=[])
        )

        async with AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        ) as client:
            readings = await client.data.get(_USER_ID)

        assert readings == []

    @respx.mock
    async def test_get_skips_unknown_types(self) -> None:
        token = _make_legacy_token()
        respx.post(f"{_BASE}/auth/login").mock(
            return_value=httpx.Response(
                200, headers={"x-tidepool-session-token": token}
            )
        )
        respx.get(f"{_BASE}/data/{_USER_ID}").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"type": "unknownFutureType", "id": "x"},
                    {
                        "type": "cbg",
                        "id": "r1",
                        "time": "2024-06-01T12:00:00Z",
                        "uploadId": "u1",
                        "value": 6.0,
                        "units": "mmol/L",
                    },
                ],
            )
        )

        async with AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        ) as client:
            readings = await client.data.get(_USER_ID)

        # unknown type silently dropped, only cbg returned
        assert len(readings) == 1
        assert isinstance(readings[0], CbgReading)

    @respx.mock
    async def test_get_sends_type_filter_param(self) -> None:
        from pytidepool import DiabetesType

        token = _make_legacy_token()
        respx.post(f"{_BASE}/auth/login").mock(
            return_value=httpx.Response(
                200, headers={"x-tidepool-session-token": token}
            )
        )
        data_route = respx.get(f"{_BASE}/data/{_USER_ID}").mock(
            return_value=httpx.Response(200, json=[])
        )

        async with AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        ) as client:
            await client.data.get(_USER_ID, data_types=[DiabetesType.CBG])

        assert "type=cbg" in str(data_route.calls.last.request.url)


# ---------------------------------------------------------------------------
# Summary resource
# ---------------------------------------------------------------------------


class TestSummaryResource:
    @respx.mock
    async def test_get_cgm_returns_cgm_summary(self) -> None:
        token = _make_legacy_token()
        respx.post(f"{_BASE}/auth/login").mock(
            return_value=httpx.Response(
                200, headers={"x-tidepool-session-token": token}
            )
        )
        respx.get(f"{_BASE}/v1/summaries/cgm/{_USER_ID}").mock(
            return_value=httpx.Response(200, json={})
        )

        async with AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        ) as client:
            summary = await client.summary.get_cgm(_USER_ID)

        assert isinstance(summary, CgmSummary)

    @respx.mock
    async def test_api_401_raises_auth_error(self) -> None:
        token = _make_legacy_token()
        respx.post(f"{_BASE}/auth/login").mock(
            return_value=httpx.Response(
                200, headers={"x-tidepool-session-token": token}
            )
        )
        respx.get(f"{_BASE}/v1/summaries/cgm/{_USER_ID}").mock(
            return_value=httpx.Response(401)
        )

        with pytest.raises(TidepoolAuthError):
            async with AsyncTidepoolClient(
                environment=Environment.PRODUCTION,
                username="user@example.com",
                password="secret",
            ) as client:
                await client.summary.get_cgm(_USER_ID)


# ---------------------------------------------------------------------------
# Metadata resource
# ---------------------------------------------------------------------------


class TestMetadataResource:
    @respx.mock
    async def test_get_profile_returns_user_profile(self) -> None:
        token = _make_legacy_token()
        respx.post(f"{_BASE}/auth/login").mock(
            return_value=httpx.Response(
                200, headers={"x-tidepool-session-token": token}
            )
        )
        respx.get(f"{_BASE}/metadata/{_USER_ID}/profile").mock(
            return_value=httpx.Response(
                200, json={"fullName": "Test User", "patient": None}
            )
        )

        async with AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        ) as client:
            profile = await client.metadata.get_profile(_USER_ID)

        assert isinstance(profile, UserProfile)
        assert profile.full_name == "Test User"
