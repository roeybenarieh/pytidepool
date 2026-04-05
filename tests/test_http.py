"""Unit tests for HTTP error mapping and AsyncHTTPClient."""

from __future__ import annotations

import pytest
import httpx

from pytidepool._http import _raise_for_status
from pytidepool._exceptions import (
    TidepoolAuthError,
    TidepoolHTTPError,
    TidepoolNotFoundError,
    TidepoolRateLimitError,
    TidepoolServerError,
)


class TestRaiseForStatus:
    def test_2xx_does_not_raise(self) -> None:
        for code in (200, 201, 204):
            _raise_for_status(httpx.Response(code))  # must not raise

    def test_401_raises_auth_error(self) -> None:
        with pytest.raises(TidepoolAuthError) as exc_info:
            _raise_for_status(httpx.Response(401))
        assert exc_info.value.status_code == 401

    def test_403_raises_auth_error(self) -> None:
        with pytest.raises(TidepoolAuthError) as exc_info:
            _raise_for_status(httpx.Response(403))
        assert exc_info.value.status_code == 403

    def test_404_raises_not_found(self) -> None:
        with pytest.raises(TidepoolNotFoundError) as exc_info:
            _raise_for_status(httpx.Response(404))
        assert exc_info.value.status_code == 404

    def test_429_raises_rate_limit(self) -> None:
        with pytest.raises(TidepoolRateLimitError) as exc_info:
            _raise_for_status(httpx.Response(429))
        assert exc_info.value.status_code == 429

    def test_429_captures_retry_after_header(self) -> None:
        response = httpx.Response(429, headers={"Retry-After": "45"})
        with pytest.raises(TidepoolRateLimitError) as exc_info:
            _raise_for_status(response)
        assert exc_info.value.retry_after == 45.0

    def test_429_retry_after_missing_is_none(self) -> None:
        with pytest.raises(TidepoolRateLimitError) as exc_info:
            _raise_for_status(httpx.Response(429))
        assert exc_info.value.retry_after is None

    def test_500_raises_server_error(self) -> None:
        with pytest.raises(TidepoolServerError) as exc_info:
            _raise_for_status(httpx.Response(500))
        assert exc_info.value.status_code == 500

    def test_503_raises_server_error(self) -> None:
        with pytest.raises(TidepoolServerError):
            _raise_for_status(httpx.Response(503))

    def test_400_raises_generic_http_error(self) -> None:
        with pytest.raises(TidepoolHTTPError) as exc_info:
            _raise_for_status(httpx.Response(400))
        # Must NOT be one of the more-specific subclasses
        assert type(exc_info.value) is TidepoolHTTPError

    def test_error_message_includes_status_code(self) -> None:
        with pytest.raises(TidepoolHTTPError) as exc_info:
            _raise_for_status(httpx.Response(503))
        assert "503" in str(exc_info.value)
