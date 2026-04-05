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
