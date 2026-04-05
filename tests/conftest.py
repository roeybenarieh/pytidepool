"""Shared fixtures for pytidepool integration tests.

Set TIDEPOOL_USERNAME and TIDEPOOL_PASSWORD in your environment before running.
All tests in this suite are skipped automatically if those variables are absent.

    export TIDEPOOL_USERNAME=your@email.com
    export TIDEPOOL_PASSWORD=yourpassword
    pytest tests/

Targets the PRODUCTION environment (api.tidepool.org) by default.
Set TIDEPOOL_ENVIRONMENT=INTEGRATION to target the integration environment instead
(your account must exist there).
"""

from __future__ import annotations

import base64
import json
import os

import pytest
import pytest_asyncio

from pytidepool import AsyncTidepoolClient, TidepoolClient, Environment


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------


def _credentials() -> tuple[str, str] | None:
    username = os.getenv("TIDEPOOL_USERNAME")
    password = os.getenv("TIDEPOOL_PASSWORD")
    if username and password:
        return username, password
    return None


def _has_credentials() -> bool:
    return _credentials() is not None


def _environment() -> Environment:
    env_name = os.getenv("TIDEPOOL_ENVIRONMENT", "PRODUCTION").upper()
    return Environment[env_name]


# Applied to every test that requires network + credentials.
requires_credentials = pytest.mark.skipif(
    not _has_credentials(),
    reason="Set TIDEPOOL_USERNAME and TIDEPOOL_PASSWORD to run integration tests",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client():
    """An AsyncTidepoolClient for each test, auto-skipped when no credentials are set."""
    creds = _credentials()
    if creds is None:
        pytest.skip("TIDEPOOL_USERNAME / TIDEPOOL_PASSWORD not set")
        return  # unreachable; satisfies type checker
    username, password = creds
    async with AsyncTidepoolClient(
        environment=_environment(),
        username=username,
        password=password,
    ) as c:
        yield c


@pytest_asyncio.fixture
async def user_id(client: AsyncTidepoolClient) -> str:
    """The Tidepool user ID for the authenticated account.

    Works with both the legacy token format (``kc:<access_jwt>:<refresh_jwt>``)
    and plain JWTs, by extracting the ``sub`` claim from the access token.
    """
    assert client._httpx_client is not None
    raw_token = await client._auth.get_valid_token(client._httpx_client)

    # Legacy token: "kc:<access_jwt>:<refresh_jwt>"
    if raw_token.startswith("kc:"):
        access_jwt = raw_token[3 : raw_token.find(":", 3 + raw_token[3:].find("."))]
    else:
        access_jwt = raw_token

    payload_b64 = access_jwt.split(".")[1]
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    return str(payload["sub"])


@pytest.fixture
def sync_client() -> TidepoolClient:
    """A TidepoolClient (sync) for each test, auto-skipped when no credentials are set."""
    creds = _credentials()
    if creds is None:
        pytest.skip("TIDEPOOL_USERNAME / TIDEPOOL_PASSWORD not set")
    username, password = creds
    with TidepoolClient(
        environment=_environment(),
        username=username,
        password=password,
    ) as c:
        yield c


@pytest.fixture
def sync_user_id(sync_client: TidepoolClient) -> str:
    """The Tidepool user ID extracted from the sync client's session token."""
    assert sync_client._async_client is not None
    assert sync_client._async_client._httpx_client is not None
    import asyncio

    raw_token = asyncio.run_coroutine_threadsafe(
        sync_client._async_client._auth.get_valid_token(
            sync_client._async_client._httpx_client
        ),
        sync_client._loop,
    ).result()

    if raw_token.startswith("kc:"):
        access_jwt = raw_token[3 : raw_token.find(":", 3 + raw_token[3:].find("."))]
    else:
        access_jwt = raw_token

    payload_b64 = access_jwt.split(".")[1]
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    return str(payload["sub"])
