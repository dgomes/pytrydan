from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class SlaveCommunicationState(IntEnum):
    """Enum for Slave Communication State."""

    NO_ERROR = 0
    ERROR_MESSAGE = 1
    COMMUNICATION_ERROR = 2


class LockState(IntEnum):
    """Enum for Lock State."""

    ENABLED = 0
    DISABLED = 1


class ChargePointTimerState(IntEnum):
    """Enum for Charge Point Timer State."""

    TIMER_OFF = 0
    TIMER_ON = 1


class DynamicState(IntEnum):
    """Enum for Dynamic Intensity Modulation State."""

    DISABLED = 0
    ENABLED = 1


class PauseDynamicState(IntEnum):
    """Enum for Pause Dynamic."""

    MODULATING = 0
    NOT_MODULATING = 1


class DynamicPowerMode(IntEnum):
    """Enum for Dynamic Power Mode."""

    TIMED_POWER_ENABLED = 0
    TIMED_POWER_DISABLED = 1
    TIMED_POWER_DISABLED_AND_EXCLUSIVE_MODE_SETTED = 2
    TIMED_POWER_DISABLED_AND_MIN_POWER_MODE_SETTED = 3
    TIMED_POWER_DISABLED_AND_GRID_FV_MODE_SETTED = 4
    TIMED_POWER_DISABLED_AND_STOP_MODE_SETTED = 5


@dataclass(slots=True)
class TrydanData:
    """Model for Trydan data."""

    charge_state: int
    ready_state: int | None
    charge_power: float
    charge_energy: float
    slave_error: SlaveCommunicationState
    charge_time: int
    house_power: int
    fv_power: float
    paused: int
    locked: LockState
    timer: ChargePointTimerState
    intensity: int
    dynamic: DynamicState
    min_intensity: int
    max_intensity: int
    pause_dynamic: PauseDynamicState
    dynamic_power_mode: DynamicPowerMode
    contracted_power: int
    firmware_version: str | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> TrydanData:
        """Initialize from the API."""
        return cls(
            charge_state=data["ChargeState"],
            ready_state=data.get("ReadyState"),
            charge_power=data["ChargePower"],
            charge_energy=data["ChargeEnergy"],
            slave_error=SlaveCommunicationState(data["SlaveError"]),
            charge_time=data["ChargeTime"],
            house_power=data["HousePower"],
            fv_power=data["FVPower"],
            paused=data["Paused"],
            locked=LockState(data["Locked"]),
            timer=ChargePointTimerState(data["Timer"]),
            intensity=data["Intensity"],
            dynamic=DynamicState(data["Dynamic"]),
            min_intensity=data["MinIntensity"],
            max_intensity=data["MaxIntensity"],
            pause_dynamic=PauseDynamicState(data["PauseDynamic"]),
            dynamic_power_mode=DynamicPowerMode(data["DynamicPowerMode"]),
            contracted_power=data["ContractedPower"],
            firmware_version=data.get("FirmwareVersion"),
        )
