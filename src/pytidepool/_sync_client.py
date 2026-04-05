from __future__ import annotations

import asyncio
import threading
from typing import Any, Coroutine, TypeVar

from pytidepool._auth import ClientCredentialsFlow, PasswordFlow
from pytidepool._client import AsyncTidepoolClient
from pytidepool._enums import Environment
from pytidepool._exceptions import TidepoolConfigurationError
from pytidepool.resources._sync import (
    SyncClinicsResource,
    SyncDataResource,
    SyncMetadataResource,
    SyncSummaryResource,
)

_T = TypeVar("_T")


class TidepoolClient:
    """Synchronous client for the Tidepool diabetes data API.

    Provides the same resource interface as :class:`TidepoolClient` but with
    plain synchronous methods — no ``async``/``await`` required.

    Internally runs a dedicated background event loop thread for the lifetime
    of the ``with`` block. All calls are marshalled into that loop via
    :func:`asyncio.run_coroutine_threadsafe`.

    Usage::

        from pytidepool import TidepoolClient, Environment

        with TidepoolClient(
            environment=Environment.PRODUCTION,
            username="user@example.com",
            password="secret",
        ) as client:
            readings = client.data.get(user_id="abc123")
            profile = client.metadata.get_profile("abc123")

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
        # Validate credentials eagerly — same rules as TidepoolClient.
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
        self._credentials = credentials

        # Initialised in __enter__, torn down in __exit__.
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._async_client: AsyncTidepoolClient | None = None

        # Cached sync resource wrappers.
        self._data: SyncDataResource | None = None
        self._clinics: SyncClinicsResource | None = None
        self._summary: SyncSummaryResource | None = None
        self._metadata: SyncMetadataResource | None = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> TidepoolClient:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            daemon=True,
            name="pytidepool-sync-loop",
        )
        self._thread.start()

        try:
            future = asyncio.run_coroutine_threadsafe(self._enter_async(), self._loop)
            self._async_client = future.result()
        except Exception:
            # If setup fails, clean up the background thread before re-raising.
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join()
            self._loop.close()
            self._loop = None
            self._thread = None
            raise

        return self

    def __exit__(self, *exc_info: Any) -> None:
        if self._async_client is not None and self._loop is not None:
            future = asyncio.run_coroutine_threadsafe(
                self._async_client.__aexit__(None, None, None),
                self._loop,
            )
            future.result()
            self._async_client = None

        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread is not None:
            self._thread.join()
            self._thread = None

        if self._loop is not None:
            self._loop.close()
            self._loop = None

        # Clear cached resources — they hold references into the closed loop.
        self._data = None
        self._clinics = None
        self._summary = None
        self._metadata = None

    async def _enter_async(self) -> AsyncTidepoolClient:
        """Create and enter an AsyncTidepoolClient on the background loop.

        Constructing AsyncTidepoolClient here (rather than in __init__) ensures
        AuthManager's asyncio.Lock binds to this loop, not the caller's loop.
        """
        creds = self._credentials
        if isinstance(creds, PasswordFlow):
            client = AsyncTidepoolClient(
                environment=self._environment,
                username=creds.username,
                password=creds.password,
                timeout=self._timeout,
            )
        else:  # ClientCredentialsFlow
            client = AsyncTidepoolClient(
                environment=self._environment,
                client_id=creds.client_id,
                client_secret=creds.client_secret,
                timeout=self._timeout,
            )
        await client.__aenter__()
        return client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run(self, coro: Coroutine[Any, Any, _T]) -> _T:
        """Submit a coroutine to the background loop and block until done."""
        if self._loop is None:
            raise RuntimeError(
                "TidepoolClient must be used as a context manager: "
                "`with TidepoolClient(...) as client:`"
            )
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def _require_entered(self) -> AsyncTidepoolClient:
        if self._async_client is None:
            raise RuntimeError(
                "TidepoolClient must be used as a context manager: "
                "`with TidepoolClient(...) as client:`"
            )
        return self._async_client

    # ------------------------------------------------------------------
    # Resource sub-clients
    # ------------------------------------------------------------------

    @property
    def data(self) -> SyncDataResource:
        """Access diabetes device data (CBG, SMBG, bolus, basal, …)."""
        if self._data is None:
            self._data = SyncDataResource(self._require_entered().data, self._run)
        return self._data

    @property
    def clinics(self) -> SyncClinicsResource:
        """Manage clinics, patients, and clinicians."""
        if self._clinics is None:
            self._clinics = SyncClinicsResource(
                self._require_entered().clinics, self._run
            )
        return self._clinics

    @property
    def summary(self) -> SyncSummaryResource:
        """Retrieve CGM/BGM time-in-range summary statistics."""
        if self._summary is None:
            self._summary = SyncSummaryResource(
                self._require_entered().summary, self._run
            )
        return self._summary

    @property
    def metadata(self) -> SyncMetadataResource:
        """Read and update user metadata collections (profile, settings, …)."""
        if self._metadata is None:
            self._metadata = SyncMetadataResource(
                self._require_entered().metadata, self._run
            )
        return self._metadata
