from __future__ import annotations

from pytidepool._enums import SummaryType
from pytidepool.models.summary import BgmSummary, CgmSummary
from pytidepool.resources._base import AsyncResource


class SummaryResource(AsyncResource):
    """Access patient glucose summary statistics."""

    async def get_cgm(self, user_id: str) -> CgmSummary:
        """Get CGM (continuous glucose) summary for a user.

        Returns time-in-range stats, average glucose, GMI, and CV
        across multiple time periods (1d, 7d, 14d, 30d).
        """
        response = await self._http.get(
            f"/v1/summaries/{SummaryType.CGM.value}/{user_id}"
        )
        return CgmSummary.model_validate(response.json())

    async def get_bgm(self, user_id: str) -> BgmSummary:
        """Get BGM (blood glucose meter) summary for a user."""
        response = await self._http.get(
            f"/v1/summaries/{SummaryType.BGM.value}/{user_id}"
        )
        return BgmSummary.model_validate(response.json())

    async def get(
        self, user_id: str, summary_type: SummaryType
    ) -> CgmSummary | BgmSummary:
        """Get summary statistics for a user by summary type."""
        if summary_type == SummaryType.CGM:
            return await self.get_cgm(user_id)
        return await self.get_bgm(user_id)
