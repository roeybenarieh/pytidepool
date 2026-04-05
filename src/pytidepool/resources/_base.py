from __future__ import annotations

from pytidepool._http import AsyncHTTPClient


class AsyncResource:
    """Base class for all API resource clients."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http
