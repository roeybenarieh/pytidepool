from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class _EnvironmentConfig:
    base_url: str
    realm: str


class Environment(Enum):
    PRODUCTION = _EnvironmentConfig(
        base_url="https://api.tidepool.org",
        realm="tidepool",
    )
    INTEGRATION = _EnvironmentConfig(
        base_url="https://int-api.tidepool.org",
        realm="integration",
    )
    DEV1 = _EnvironmentConfig(
        base_url="https://dev1-api.tidepool.org",
        realm="dev1",
    )
    QA1 = _EnvironmentConfig(
        base_url="https://qa1-api.tidepool.org",
        realm="qa1",
    )
    QA2 = _EnvironmentConfig(
        base_url="https://qa2-api.tidepool.org",
        realm="qa2",
    )
    QA3 = _EnvironmentConfig(
        base_url="https://qa3-api.tidepool.org",
        realm="qa3",
    )
    QA4 = _EnvironmentConfig(
        base_url="https://qa4-api.tidepool.org",
        realm="qa4",
    )
    QA5 = _EnvironmentConfig(
        base_url="https://qa5-api.tidepool.org",
        realm="qa5",
    )

    @property
    def base_url(self) -> str:
        return self.value.base_url

    @property
    def realm(self) -> str:
        return self.value.realm


class DiabetesType(str, Enum):
    CBG = "cbg"
    SMBG = "smbg"
    BOLUS = "bolus"
    BASAL = "basal"
    DEVICE_EVENT = "deviceEvent"
    PUMP_SETTINGS = "pumpSettings"
    WIZARD = "wizard"


class SummaryType(str, Enum):
    CGM = "cgm"
    BGM = "bgm"
