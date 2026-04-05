from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass
from typing import Union

import httpx

from pytidepool._enums import Environment
from pytidepool._exceptions import TidepoolAuthError
from pytidepool.models.auth import TokenResponse


@dataclass(frozen=True)
class PasswordFlow:
    """Authenticate with username + password via the legacy Tidepool /auth/login endpoint.

    This is the simplest way to authenticate for end-user accounts. It uses
    Tidepool's own auth proxy (not a direct Keycloak call), so no OAuth2
    ``client_id`` registration is required.
    """

    username: str
    password: str


@dataclass(frozen=True)
class KeycloakPasswordFlow:
    """Authenticate with username + password via the Keycloak password grant.

    Requires a ``client_id`` that is registered with Tidepool and has the
    password grant type enabled. Most third-party clients should use
    :class:`PasswordFlow` instead.
    """

    username: str
    password: str
    client_id: str


@dataclass(frozen=True)
class ClientCredentialsFlow:
    """Authenticate server-to-server via the Keycloak client_credentials grant."""

    client_id: str
    client_secret: str


Credentials = Union[PasswordFlow, KeycloakPasswordFlow, ClientCredentialsFlow]


def _parse_legacy_token(raw_token: str) -> TokenResponse:
    """Parse a legacy Tidepool session token into a TokenResponse.

    Legacy tokens have the format ``kc:<access_jwt>:<refresh_jwt>``.
    The expiry is extracted from the access JWT's ``exp``/``iat`` claims.
    """
    if raw_token.startswith("kc:"):
        # Split on ":" but the JWTs themselves contain "." not ":", so a
        # simple split at the second colon works.
        without_prefix = raw_token[3:]  # strip "kc:"
        # The access JWT ends at the second "." after the second colon.
        # Format: kc:<header>.<payload>.<sig>:<header>.<payload>.<sig>
        # Both tokens use base64url, so no ":" inside them — safe to split on ":".
        colon_idx = without_prefix.find(":", without_prefix.find("."))
        if colon_idx != -1:
            access_jwt = without_prefix[:colon_idx]
            refresh_jwt = without_prefix[colon_idx + 1 :]
        else:
            access_jwt = without_prefix
            refresh_jwt = None

        try:
            payload_b64 = access_jwt.split(".")[1]
            payload_b64 += "=" * (4 - len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            expires_in = int(payload.get("exp", 0)) - int(payload.get("iat", 0))
            refresh_expires_in: int | None = None
            if refresh_jwt:
                ref_b64 = refresh_jwt.split(".")[1]
                ref_b64 += "=" * (4 - len(ref_b64) % 4)
                ref_payload = json.loads(base64.urlsafe_b64decode(ref_b64))
                refresh_expires_in = int(ref_payload.get("exp", 0)) - int(
                    ref_payload.get("iat", 0)
                )
        except Exception:
            expires_in = 720  # 12 minutes default
            refresh_jwt = None
            refresh_expires_in = None

        return TokenResponse(
            access_token=raw_token,
            expires_in=expires_in,
            refresh_token=refresh_jwt,
            refresh_expires_in=refresh_expires_in,
        )

    # Unrecognised format — treat as opaque token with a 12-minute TTL.
    return TokenResponse(access_token=raw_token, expires_in=720)


class AuthManager:
    """Manages token lifecycle: fetch, cache, and refresh with concurrency safety."""

    def __init__(self, environment: Environment, credentials: Credentials) -> None:
        self._environment = environment
        self._credentials = credentials
        self._token: TokenResponse | None = None
        self._lock = asyncio.Lock()

    @property
    def _keycloak_token_url(self) -> str:
        return (
            f"{self._environment.base_url}/realms/{self._environment.realm}"
            "/protocol/openid-connect/token"
        )

    @property
    def _legacy_login_url(self) -> str:
        return f"{self._environment.base_url}/auth/login"

    # ------------------------------------------------------------------
    # Token fetch
    # ------------------------------------------------------------------

    async def _fetch_token(self, http: httpx.AsyncClient) -> TokenResponse:
        creds = self._credentials

        if isinstance(creds, PasswordFlow):
            return await self._fetch_legacy(http, creds)
        if isinstance(creds, KeycloakPasswordFlow):
            return await self._fetch_keycloak(
                http,
                data={
                    "grant_type": "password",
                    "client_id": creds.client_id,
                    "username": creds.username,
                    "password": creds.password,
                },
            )
        # ClientCredentialsFlow
        return await self._fetch_keycloak(
            http,
            data={
                "grant_type": "client_credentials",
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
            },
        )

    async def _fetch_legacy(
        self, http: httpx.AsyncClient, creds: PasswordFlow
    ) -> TokenResponse:
        encoded = base64.b64encode(
            f"{creds.username}:{creds.password}".encode()
        ).decode()
        response = await http.post(
            self._legacy_login_url,
            headers={"Authorization": f"Basic {encoded}"},
        )
        if response.status_code in (401, 403):
            raise TidepoolAuthError(
                f"Authentication failed: {response.text}",
                status_code=response.status_code,
                response=response,
            )
        response.raise_for_status()
        raw_token = response.headers.get("x-tidepool-session-token", "")
        if not raw_token:
            raise TidepoolAuthError(
                "Login succeeded but no x-tidepool-session-token header was returned.",
                status_code=response.status_code,
                response=response,
            )
        return _parse_legacy_token(raw_token)

    async def _fetch_keycloak(
        self, http: httpx.AsyncClient, data: dict[str, str]
    ) -> TokenResponse:
        response = await http.post(self._keycloak_token_url, data=data)
        if response.status_code in (401, 403):
            raise TidepoolAuthError(
                f"Authentication failed: {response.text}",
                status_code=response.status_code,
                response=response,
            )
        response.raise_for_status()
        return TokenResponse.model_validate(response.json())

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    async def _refresh_token(
        self, http: httpx.AsyncClient, refresh_token: str
    ) -> TokenResponse:
        creds = self._credentials
        if isinstance(creds, PasswordFlow):
            # Legacy sessions don't have a dedicated refresh endpoint;
            # fall through to re-login by raising so the caller falls back.
            raise NotImplementedError("Legacy auth does not support token refresh")
        form: dict[str, str] = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": creds.client_id,
        }
        if isinstance(creds, ClientCredentialsFlow):
            form["client_secret"] = creds.client_secret
        response = await http.post(self._keycloak_token_url, data=form)
        response.raise_for_status()
        return TokenResponse.model_validate(response.json())

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def get_user_id(self, http: httpx.AsyncClient) -> str:
        """Return the authenticated user's Tidepool user ID (JWT ``sub`` claim)."""
        raw_token = await self.get_valid_token(http)
        # Legacy format: "kc:<access_jwt>:<refresh_jwt>"
        if raw_token.startswith("kc:"):
            without_prefix = raw_token[3:]
            colon_idx = without_prefix.find(":", without_prefix.find("."))
            access_jwt = without_prefix[:colon_idx] if colon_idx != -1 else without_prefix
        else:
            access_jwt = raw_token
        payload_b64 = access_jwt.split(".")[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return str(payload["sub"])

    async def get_valid_token(self, http: httpx.AsyncClient) -> str:
        """Return a valid access token, refreshing or re-authenticating as needed.

        Uses double-checked locking to prevent redundant refreshes under load.
        """
        if self._token is not None and not self._token.is_expired():
            return self._token.access_token

        async with self._lock:
            # Re-check — another coroutine may have refreshed while we waited.
            if self._token is not None and not self._token.is_expired():
                return self._token.access_token

            # Try token refresh first if a refresh token is available.
            if (
                self._token is not None
                and self._token.refresh_token is not None
                and not self._token.refresh_token_is_expired()
            ):
                try:
                    refreshed = await self._refresh_token(
                        http, self._token.refresh_token
                    )
                    self._token = refreshed
                    return refreshed.access_token
                except Exception:
                    pass  # fall through to full re-authentication

            fetched = await self._fetch_token(http)
            self._token = fetched
            return fetched.access_token
