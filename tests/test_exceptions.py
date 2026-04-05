"""Unit tests for the exception hierarchy."""

from __future__ import annotations

import pytest
import httpx

from pytidepool._exceptions import (
    TidepoolError,
    TidepoolHTTPError,
    TidepoolAuthError,
    TidepoolNotFoundError,
    TidepoolRateLimitError,
    TidepoolServerError,
    TidepoolConfigurationError,
)


class TestExceptionHierarchy:
    def test_all_http_errors_are_tidepool_errors(self) -> None:
        for cls in (
            TidepoolHTTPError,
            TidepoolAuthError,
            TidepoolNotFoundError,
            TidepoolRateLimitError,
            TidepoolServerError,
        ):
            assert issubclass(cls, TidepoolError)
            assert issubclass(cls, TidepoolHTTPError)

    def test_configuration_error_is_tidepool_error(self) -> None:
        assert issubclass(TidepoolConfigurationError, TidepoolError)

    def test_http_error_carries_status_code(self) -> None:
        response = httpx.Response(404)
        exc = TidepoolNotFoundError("not found", status_code=404, response=response)
        assert exc.status_code == 404
        assert exc.response is response

    def test_rate_limit_error_carries_retry_after(self) -> None:
        response = httpx.Response(429)
        exc = TidepoolRateLimitError(
            "rate limited", status_code=429, response=response, retry_after=60.0
        )
        assert exc.retry_after == 60.0

    def test_rate_limit_error_retry_after_optional(self) -> None:
        response = httpx.Response(429)
        exc = TidepoolRateLimitError("rate limited", status_code=429, response=response)
        assert exc.retry_after is None

    def test_catchable_as_base_class(self) -> None:
        with pytest.raises(TidepoolError):
            raise TidepoolAuthError(
                "unauthorized", status_code=401, response=httpx.Response(401)
            )

    def test_catchable_as_http_error(self) -> None:
        with pytest.raises(TidepoolHTTPError):
            raise TidepoolServerError(
                "server error", status_code=500, response=httpx.Response(500)
            )
