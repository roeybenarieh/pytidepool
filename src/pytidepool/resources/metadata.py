from __future__ import annotations

from typing import Any

from pytidepool.models.metadata import UserProfile
from pytidepool.resources._base import AsyncResource


class MetadataResource(AsyncResource):
    """Access and update user metadata collections."""

    async def get(self, user_id: str | None = None, collection: str = "profile") -> dict[str, Any]:
        """Fetch a metadata collection for a user.

        Common collection names: ``profile``, ``settings``, ``preferences``.
        Use ``client.metadata.get_collections()`` to list valid names.

        Args:
            user_id: Tidepool user ID. Defaults to the authenticated user.
            collection: Metadata collection name.
        """
        uid = await self._resolve_user_id(user_id)
        response = await self._http.get(f"/metadata/{uid}/{collection}")
        return response.json()  # type: ignore[no-any-return]

    async def get_profile(self, user_id: str | None = None) -> UserProfile:
        """Fetch and parse the ``profile`` metadata collection as a :class:`UserProfile`.

        Args:
            user_id: Tidepool user ID. Defaults to the authenticated user.
        """
        data = await self.get(user_id, "profile")
        return UserProfile.model_validate(data)

    async def update(self, collection: str, data: dict[str, Any], *, user_id: str | None = None) -> None:
        """Update (PUT) a metadata collection for a user.

        Args:
            collection: Metadata collection name.
            data: New collection data.
            user_id: Tidepool user ID. Defaults to the authenticated user.
        """
        uid = await self._resolve_user_id(user_id)
        await self._http.put(f"/metadata/{uid}/{collection}", json=data)

    async def get_collections(self) -> list[str]:
        """Return the list of valid metadata collection names."""
        response = await self._http.get("/metadata/collections")
        body = response.json()
        return body if isinstance(body, list) else []
