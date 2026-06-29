from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from ..exceptions import ChargeStateInvalid


class ChargeState(IntEnum):
    """Enum for Charge State."""

    NOT_CONNECTED = 0
    CONNECTED_NOT_CHARGING = 1
    CONNECTED_CHARGING = 2
    SYSTEM_FAILURE_OR_LEAK_DETECTED = 4
    PILOT_SHORT = 4
    CONTROL_PILOT_OR_GROUND_FAILURE = 5
    GENERAL_FAULT = 5
    VENTILATION_REQUIRED = 6
    VENTILATION = 6


class ReadyState(IntEnum):
    """Enum for Ready State."""

    NOT_READY = 0
    READY = 1


class SlaveCommunicationState(IntEnum):
    """Enum for Slave Communication State."""

    NO_ERROR = 0
    COMMUNICATION = 1
    READING = 2
    SLAVE = 3
    WAITING_WIFI = 4
    WAITING_COMMUNICATION = 5
    WRONG_IP = 6
    SLAVE_NOT_FOUND = 7
    WRONG_SLAVE = 8
    NO_RESPONSE = 9
    CLAMP_NOT_CONNECTED = 10
    # MODBUS_ERRORS
    ILLEGAL_FUNCTION = 21
    ILLEGAL_DATA_ADDRESS = 22
    ILLEGAL_DATA_VALUE = 23
    SERVER_DEVICE_FAILURE = 24
    ACKNOWLEDGE = 25
    SERVER_DEVICE_BUSY = 26
    NEGATIVE_ACKNOWLEDGE = 27
    MEMORY_PARITY_ERROR = 28
    GATEWAY_PATH_UNAVAILABLE = 30
    GATEWAY_TARGET_NO_RESP = 31
    SERVER_RTU_INACTIVE244_TIMEOUT = 32
    INVALID_SERVER = 245
    CRC_ERROR = 246
    FC_MISMATCH = 247
    SERVER_ID_MISMATCH = 248
    PACKET_LENGTH_ERROR = 249
    PARAMETER_COUNT_ERROR = 250
    PARAMETER_LIMIT_ERROR = 251
    REQUEST_QUEUE_FULL = 252
    ILLEGAL_IP_OR_PORT = 253
    IP_CONNECTION_FAILED = 254
    TCP_HEAD_MISMATCH = 255
    EMPTY_MESSAGE = 256
    UNDEFINED_ERROR = 257


class PauseState(IntEnum):
    """Enum for Pause State."""

    PAUSED = 1
    NOT_PAUSED = 0


class LockState(IntEnum):
    """Enum for Lock State."""

    ENABLED = 1
    DISABLED = 0


class ChargePointTimerState(IntEnum):
    """Enum for Charge Point Timer State."""

    TIMER_OFF = 0
    TIMER_ON = 1


class ChargeMode(IntEnum):
    """Enum for Charge Mode."""

    MONOPHASIC = 0
    THREEPHASIC = 1
    MIXED = 2


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
    """Application or V2C cloud profile mode."""
    TIMED_POWER_DISABLED_AND_FV_MIN_MODE_SETTED = 2
    """FV + min power mode."""
    TIMED_POWER_DISABLED_AND_FV_EXCL_MODE_SETTED = 3
    """FV exclusive mode."""
    TIMED_POWER_DISABLED_AND_FV_GRID_MODE_SETTED = 4
    """FV + grid mode."""
    TIMED_POWER_DISABLED_AND_STOP_MODE_SETTED = 5
    """Stop mode."""


@dataclass(slots=True)
class TrydanData:
    """Model for Trydan data."""

    ID: str | None
    charge_state: ChargeState
    ready_state: ReadyState
    charge_power: float
    voltage_installation: int | None
    charge_energy: float
    charge_mode: ChargeMode | None
    slave_error: SlaveCommunicationState
    charge_time: int
    house_power: int
    fv_power: float
    battery_power: float | None
    paused: PauseState
    locked: LockState
    timer: ChargePointTimerState
    intensity: int
    dynamic: DynamicState
    min_intensity: int
    max_intensity: int
    pause_dynamic: PauseDynamicState
    light_led: int | None
    logo_led: int | None
    dynamic_power_mode: DynamicPowerMode
    contracted_power: int
    firmware_version: str | None
    SSID: str | None
    IP: str | None
    signal_status: int | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> TrydanData:
        """Initialize from the API."""
        try:
            charge_state = ChargeState(data["ChargeState"])
        except ValueError as err:
            raise ChargeStateInvalid(
                f"Invalid charge state: {data['ChargeState']}"
            ) from err

        return cls(
            ID=data.get("ID"),
            charge_state=charge_state,
            ready_state=ReadyState(data.get("ReadyState", 0)),
            charge_power=data["ChargePower"],
            voltage_installation=data.get("VoltageInstallation"),
            charge_energy=data["ChargeEnergy"],
            charge_mode=ChargeMode(data["ChargeMode"])
            if "ChargeMode" in data
            else None,
            slave_error=SlaveCommunicationState(data["SlaveError"]),
            charge_time=data["ChargeTime"],
            house_power=data["HousePower"],
            fv_power=data["FVPower"],
            battery_power=data.get("BatteryPower"),
            paused=PauseState(data["Paused"]),
            locked=LockState(data["Locked"]),
            timer=ChargePointTimerState(data["Timer"]),
            intensity=data["Intensity"],
            dynamic=DynamicState(data["Dynamic"]),
            min_intensity=data["MinIntensity"],
            max_intensity=data["MaxIntensity"],
            pause_dynamic=PauseDynamicState(data["PauseDynamic"]),
            light_led=data.get("LightLED"),
            logo_led=data.get("LogoLED"),
            dynamic_power_mode=DynamicPowerMode(data["DynamicPowerMode"]),
            contracted_power=data["ContractedPower"],
            firmware_version=data.get("FirmwareVersion"),
            SSID=data.get("SSID"),
            IP=data.get("IP"),
            signal_status=data.get("SignalStatus"),
        )
