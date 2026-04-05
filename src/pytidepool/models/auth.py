from __future__ import annotations

import time

from pydantic import BaseModel, PrivateAttr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: str | None = None
    refresh_expires_in: int | None = None
    scope: str | None = None
    id_token: str | None = None

    # Private attribute: unix timestamp recorded when this instance was created.
    _issued_at: float = PrivateAttr(default_factory=time.time)

    def is_expired(self, buffer_seconds: int = 30) -> bool:
        """Return True if the access token has expired (or will expire within buffer_seconds)."""
        return time.time() >= self._issued_at + self.expires_in - buffer_seconds

    def refresh_token_is_expired(self, buffer_seconds: int = 30) -> bool:
        """Return True if the refresh token has expired."""
        if self.refresh_token is None or self.refresh_expires_in is None:
            return True
        return time.time() >= self._issued_at + self.refresh_expires_in - buffer_seconds
