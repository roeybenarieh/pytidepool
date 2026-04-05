from __future__ import annotations

from typing import Any

from pytidepool.models.metadata import UserProfile
from pytidepool.resources._base import AsyncResource


class MetadataResource(AsyncResource):
    """Access and update user metadata collections."""

    async def get(self, user_id: str, collection: str) -> dict[str, Any]:
        """Fetch a metadata collection for a user.

        Common collection names: ``profile``, ``settings``, ``preferences``.
        Use ``client.metadata.get_collections()`` to list valid names.
        """
        response = await self._http.get(f"/metadata/{user_id}/{collection}")
        return response.json()  # type: ignore[no-any-return]

    async def get_profile(self, user_id: str) -> UserProfile:
        """Fetch and parse the ``profile`` metadata collection as a :class:`UserProfile`."""
        data = await self.get(user_id, "profile")
        return UserProfile.model_validate(data)

    async def update(self, user_id: str, collection: str, data: dict[str, Any]) -> None:
        """Update (PUT) a metadata collection for a user."""
        await self._http.put(f"/metadata/{user_id}/{collection}", json=data)

    async def get_collections(self) -> list[str]:
        """Return the list of valid metadata collection names."""
        response = await self._http.get("/metadata/collections")
        body = response.json()
        return body if isinstance(body, list) else []
