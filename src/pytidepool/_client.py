from __future__ import annotations

import asyncio
from typing import Any, Coroutine, TypeVar

import httpx

from pytidepool._auth import AuthManager, ClientCredentialsFlow, PasswordFlow
from pytidepool._enums import Environment
from pytidepool._exceptions import TidepoolConfigurationError
from pytidepool._http import AsyncHTTPClient
from pytidepool.resources.clinics import ClinicsResource
from pytidepool.resources.data import DataResource
from pytidepool.resources.metadata import MetadataResource
from pytidepool.resources.summary import SummaryResource

_T = TypeVar("_T")


class AsyncTidepoolClient:
    """Async client for the Tidepool diabetes data API.

    Use as an async context manager to ensure the underlying HTTP connection
    pool is properly opened and closed::

        async with AsyncTidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        ) as client:
            readings = await client.data.get(user_id="...")

    Attributes:
        data: Access diabetes device data.
        clinics: Manage clinics, patients, and clinicians.
        summary: Retrieve patient glucose summary statistics.
        metadata: Read and update user metadata/profiles.
    """

    def __init__(
        self,
        *,
        environment: Environment = Environment.PRODUCTION,
        username: str | None = None,
        password: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        if username is not None and password is not None:
            credentials: PasswordFlow | ClientCredentialsFlow = PasswordFlow(
                username=username, password=password
            )
        elif client_id is not None and client_secret is not None:
            credentials = ClientCredentialsFlow(
                client_id=client_id, client_secret=client_secret
            )
        else:
            raise TidepoolConfigurationError(
                "Provide either (username, password) or (client_id, client_secret)."
            )

        self._environment = environment
        self._timeout = timeout
        self._auth = AuthManager(environment=environment, credentials=credentials)
        self._httpx_client: httpx.AsyncClient | None = None
        self._http: AsyncHTTPClient | None = None

        # Cached resource instances
        self._data: DataResource | None = None
        self._clinics: ClinicsResource | None = None
        self._summary: SummaryResource | None = None
        self._metadata: MetadataResource | None = None

    # ------------------------------------------------------------------
    # Async context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> AsyncTidepoolClient:
        self._httpx_client = httpx.AsyncClient(
            base_url=self._environment.base_url,
            timeout=self._timeout,
        )
        self._http = AsyncHTTPClient(self._httpx_client, self._auth)
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._httpx_client is not None:
            await self._httpx_client.aclose()
            self._httpx_client = None
            self._http = None

    # ------------------------------------------------------------------
    # Resource sub-clients
    # ------------------------------------------------------------------

    def _get_http(self) -> AsyncHTTPClient:
        if self._http is None:
            raise RuntimeError(
                "AsyncTidepoolClient must be used as an async context manager: "
                "`async with AsyncTidepoolClient(...) as client:`"
            )
        return self._http

    @property
    def data(self) -> DataResource:
        """Access diabetes device data (CBG, SMBG, bolus, basal, …)."""
        if self._data is None:
            self._data = DataResource(self._get_http())
        return self._data

    @property
    def clinics(self) -> ClinicsResource:
        """Manage clinics, patients, and clinicians."""
        if self._clinics is None:
            self._clinics = ClinicsResource(self._get_http())
        return self._clinics

    @property
    def summary(self) -> SummaryResource:
        """Retrieve CGM/BGM time-in-range summary statistics."""
        if self._summary is None:
            self._summary = SummaryResource(self._get_http())
        return self._summary

    @property
    def metadata(self) -> MetadataResource:
        """Read and update user metadata collections (profile, settings, …)."""
        if self._metadata is None:
            self._metadata = MetadataResource(self._get_http())
        return self._metadata

    async def get_user_id(self) -> str:
        """Return the authenticated user's Tidepool user ID.

        Extracted from the ``sub`` claim of the current access token — no
        extra HTTP request is made beyond the initial login.
        """
        if self._httpx_client is None:
            raise RuntimeError(
                "AsyncTidepoolClient must be used as an async context manager: "
                "`async with AsyncTidepoolClient(...) as client:`"
            )
        return await self._auth._get_user_id(self._httpx_client)

    # ------------------------------------------------------------------
    # Synchronous convenience
    # ------------------------------------------------------------------

    @staticmethod
    def run_sync(coro: Coroutine[Any, Any, _T]) -> _T:
        """Run an async coroutine synchronously.

        Useful for scripts and notebooks::

            readings = AsyncTidepoolClient.run_sync(fetch_readings())
        """
        return asyncio.run(coro)
