from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


class TidepoolError(Exception):
    """Base exception for all pytidepool errors."""


class TidepoolConfigurationError(TidepoolError):
    """Raised when the client is misconfigured (e.g. missing credentials)."""


class TidepoolHTTPError(TidepoolError):
    """Raised for non-2xx HTTP responses."""

    def __init__(
        self, message: str, *, status_code: int, response: "httpx.Response"
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class TidepoolAuthError(TidepoolHTTPError):
    """Raised for 401/403 responses — authentication or authorization failure."""


class TidepoolNotFoundError(TidepoolHTTPError):
    """Raised for 404 responses."""


class TidepoolRateLimitError(TidepoolHTTPError):
    """Raised for 429 responses. Check .retry_after for the suggested wait (seconds)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        response: "httpx.Response",
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response=response)
        self.retry_after = retry_after


class TidepoolServerError(TidepoolHTTPError):
    """Raised for 5xx responses."""
