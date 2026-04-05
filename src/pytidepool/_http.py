from __future__ import annotations

from typing import Any

import httpx

from pytidepool._auth import AuthManager
from pytidepool._exceptions import (
    TidepoolAuthError,
    TidepoolHTTPError,
    TidepoolNotFoundError,
    TidepoolRateLimitError,
    TidepoolServerError,
)


def _raise_for_status(response: httpx.Response) -> None:
    """Map HTTP error responses to typed pytidepool exceptions."""
    if response.is_success:
        return
    status = response.status_code
    message = f"HTTP {status}: {response.text[:200]}"
    if status in (401, 403):
        raise TidepoolAuthError(message, status_code=status, response=response)
    if status == 404:
        raise TidepoolNotFoundError(message, status_code=status, response=response)
    if status == 429:
        retry_after_raw = response.headers.get("Retry-After")
        retry_after = float(retry_after_raw) if retry_after_raw else None
        raise TidepoolRateLimitError(
            message, status_code=status, response=response, retry_after=retry_after
        )
    if status >= 500:
        raise TidepoolServerError(message, status_code=status, response=response)
    raise TidepoolHTTPError(message, status_code=status, response=response)


class AsyncHTTPClient:
    """Thin httpx wrapper that injects auth headers and maps errors."""

    def __init__(self, http: httpx.AsyncClient, auth: AuthManager) -> None:
        self._http = http
        self._auth = auth

    async def _auth_headers(self) -> dict[str, str]:
        token = await self._auth.get_valid_token(self._http)
        return {"x-tidepool-session-token": token}

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        headers = {**await self._auth_headers(), **kwargs.pop("headers", {})}
        response = await self._http.get(path, headers=headers, **kwargs)
        _raise_for_status(response)
        return response

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        headers = {**await self._auth_headers(), **kwargs.pop("headers", {})}
        response = await self._http.post(path, headers=headers, **kwargs)
        _raise_for_status(response)
        return response

    async def put(self, path: str, **kwargs: Any) -> httpx.Response:
        headers = {**await self._auth_headers(), **kwargs.pop("headers", {})}
        response = await self._http.put(path, headers=headers, **kwargs)
        _raise_for_status(response)
        return response

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        headers = {**await self._auth_headers(), **kwargs.pop("headers", {})}
        response = await self._http.delete(path, headers=headers, **kwargs)
        _raise_for_status(response)
        return response
