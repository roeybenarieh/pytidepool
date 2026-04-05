from __future__ import annotations

from typing import Any, Callable, Coroutine

from pytidepool._http import AsyncHTTPClient


class AsyncResource:
    """Base class for all API resource clients."""

    def __init__(
        self,
        http: AsyncHTTPClient,
        get_user_id: Callable[[], Coroutine[Any, Any, str]] | None = None,
    ) -> None:
        self._http = http
        self._get_user_id = get_user_id

    async def _resolve_user_id(self, user_id: str | None) -> str:
        """Return user_id if provided, otherwise call the injected resolver."""
        if user_id is not None:
            return user_id
        if self._get_user_id is None:
            raise RuntimeError(
                "user_id is required but no authenticated user is available."
            )
        return await self._get_user_id()
