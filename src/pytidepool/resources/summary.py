from __future__ import annotations

from pytidepool._enums import SummaryType
from pytidepool.models.summary import BgmSummary, CgmSummary
from pytidepool.resources._base import AsyncResource


class SummaryResource(AsyncResource):
    """Access patient glucose summary statistics."""

    async def get_cgm(self, user_id: str | None = None) -> CgmSummary:
        """Get CGM (continuous glucose) summary for a user.

        Returns time-in-range stats, average glucose, GMI, and CV
        across multiple time periods (1d, 7d, 14d, 30d).

        Args:
            user_id: Tidepool user ID. Defaults to the authenticated user.
        """
        uid = await self._resolve_user_id(user_id)
        response = await self._http.get(
            f"/v1/summaries/{SummaryType.CGM.value}/{uid}"
        )
        return CgmSummary.model_validate(response.json())

    async def get_bgm(self, user_id: str | None = None) -> BgmSummary:
        """Get BGM (blood glucose meter) summary for a user.

        Args:
            user_id: Tidepool user ID. Defaults to the authenticated user.
        """
        uid = await self._resolve_user_id(user_id)
        response = await self._http.get(
            f"/v1/summaries/{SummaryType.BGM.value}/{uid}"
        )
        return BgmSummary.model_validate(response.json())

    async def get(
        self, summary_type: SummaryType, user_id: str | None = None
    ) -> CgmSummary | BgmSummary:
        """Get summary statistics for a user by summary type.

        Args:
            summary_type: CGM or BGM.
            user_id: Tidepool user ID. Defaults to the authenticated user.
        """
        if summary_type == SummaryType.CGM:
            return await self.get_cgm(user_id)
        return await self.get_bgm(user_id)
