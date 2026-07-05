from __future__ import annotations

import logging
from collections.abc import Callable
from enum import IntEnum
from http import HTTPStatus
from typing import Any

import httpx
import orjson
from httpcore import ConnectTimeout
from tenacity import retry, retry_if_exception_type, wait_random_exponential

from .const import API_TIMEOUT, KEYWORDS
from .exceptions import (
    TrydanCommunicationError,
    TrydanInvalidKeyword,
    TrydanInvalidResponse,
    TrydanInvalidValue,
    TrydanRetryLater,
)
from .models.trydan import (
    ChargeMode,
    ChargePointTimerState,
    ChargeState,
    DynamicPowerMode,
    DynamicState,
    LockState,
    PauseDynamicState,
    PauseState,
    ReadyState,
    TrydanData,
)

KeywordValue = str | int | IntEnum


def _coerce_int(value: object) -> int | None:
    """Return the integer value for supported keyword inputs."""
    if isinstance(value, IntEnum):
        return value.value
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    if isinstance(value, float):
        return round(value)
    return None


def _is_enum_value(enum: type[IntEnum], value: object) -> bool:
    """Return whether value can be serialized as an enum member."""
    raw_value = _coerce_int(value)
    if raw_value is None:
        return False

    try:
        enum(raw_value)
    except ValueError:
        return False
    return True


def _is_intensity(value: object) -> bool:
    """Return whether value is a valid intensity."""
    current = _coerce_int(value)
    if current is None:
        return False
    return 6 <= current <= 32


def _is_positive_int(value: object) -> bool:
    """Return whether value is a positive integer."""
    current = _coerce_int(value)
    if current is None:
        return False
    return current > 0


def _is_percentage(value: object) -> bool:
    """Return whether value is a valid percentage."""
    percentage = _coerce_int(value)
    if percentage is None:
        return False
    return 0 <= percentage <= 100


def _is_int(value: object) -> bool:
    """Return whether value is a integer, can be negative."""
    current = _coerce_int(value)
    return current is not None


def _serialize_keyword_value(value: KeywordValue) -> str:
    """Serialize keyword values for the Trydan write endpoint."""
    if isinstance(value, IntEnum):
        return str(value.value)
    return str(value)


VALIDATION: dict[str, Callable[[object], bool]] = {
    "ChargeMode": lambda value: _is_enum_value(ChargeMode, value),
    "ChargeState": lambda value: _is_enum_value(ChargeState, value),
    "ContractedPower": _is_int,
    "Dynamic": lambda value: _is_enum_value(DynamicState, value),
    "DynamicPowerMode": lambda value: _is_enum_value(DynamicPowerMode, value),
    "Intensity": _is_intensity,
    "LightLED": _is_percentage,
    "Locked": lambda value: _is_enum_value(LockState, value),
    "LogoLED": _is_percentage,
    "MaxIntensity": _is_intensity,
    "MinIntensity": _is_intensity,
    "PauseDynamic": lambda value: _is_enum_value(PauseDynamicState, value),
    "Paused": lambda value: _is_enum_value(PauseState, value),
    "Timer": lambda value: _is_enum_value(ChargePointTimerState, value),
    "VoltageInstallation": _is_positive_int,
}

_LOGGER = logging.getLogger(__name__)


class _TrydanKeywordUnavailable(Exception):
    """Raised when a keyword read endpoint is not available."""


class Trydan:
    """Class for communicating with Trydan."""

    def __init__(
        self,
        host: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize."""
        self._host = host
        self._client = client if client is not None else httpx.AsyncClient()
        self._owns_client = client is None
        self._timeout = API_TIMEOUT
        self._data: TrydanData | None = None
        self._realtime_data_missing_keywords: set[str] | None = None
        self._unavailable_realtime_data_keywords: set[str] = set()
        self.raw_data: dict[str, bytes | int] | None = None

    async def __aenter__(self) -> Trydan:
        """Return this client when used as an async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Close any internally-created HTTP client."""
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client if this instance owns it."""
        if self._owns_client:
            await self._client.aclose()

    @retry(
        retry=retry_if_exception_type(
            (
                httpx.NetworkError,
                httpx.TimeoutException,
                httpx.RemoteProtocolError,
            )
        ),
        wait=wait_random_exponential(multiplier=2, max=3),
    )
    async def request(self, endpoint: str) -> httpx.Response:
        """Make a request to Trydan."""
        return await self._request(endpoint)

    async def _request(
        self,
        url: str,
    ) -> httpx.Response:
        """Make a request to Trydan."""
        _LOGGER.debug("Requesting %s with timeout %s", url, self._timeout)
        response = await self._client.get(
            url,
            timeout=self._timeout,
        )

        self.raw_data = {
            "content": response.content,
            "status_code": response.status_code,
        }

        status_code = response.status_code
        if status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
            raise TrydanCommunicationError(
                f"Failed for {url} with status {status_code}"
            )
        if status_code != HTTPStatus.OK:
            raise TrydanInvalidResponse(f"Failed for {url} with status {status_code}")

        return response

    async def _json_request(self, end_point: str) -> dict[str, Any]:
        """Make a request to Trydan and return the JSON response."""
        response = await self._request(end_point)
        try:
            data = orjson.loads(response.content)
        except orjson.JSONDecodeError as err:
            _LOGGER.error(
                "Error decoding JSON response from Trydan: %r", response.content
            )
            raise TrydanInvalidResponse(
                "Error decoding JSON response from Trydan"
            ) from err
        if not isinstance(data, dict):
            raise TrydanInvalidResponse("Expected JSON object response from Trydan")
        return data

    async def _read_keyword(self, keyword: str) -> Any:
        """Read a single keyword from Trydan."""
        try:
            response = await self._request(f"http://{self._host}/read/{keyword}")
        except TrydanInvalidResponse as err:
            if (
                self.raw_data is not None
                and self.raw_data.get("status_code") == HTTPStatus.NOT_FOUND
            ):
                raise _TrydanKeywordUnavailable from err
            raise
        return self._parse_keyword_value(response.text.strip())

    @staticmethod
    def _parse_keyword_value(value: str) -> int | float | str:
        """Parse a text keyword response into a scalar value."""
        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            return value

    async def _with_missing_realtime_data_keywords(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Fill RealTimeData with keywords that require the read endpoint."""
        missing_keywords = KEYWORDS.difference(data).difference(
            self._unavailable_realtime_data_keywords
        )
        if self._realtime_data_missing_keywords is None:
            self._realtime_data_missing_keywords = missing_keywords
        else:
            self._realtime_data_missing_keywords.update(missing_keywords)

        for keyword in sorted(self._realtime_data_missing_keywords):
            try:
                data[keyword] = await self._read_keyword(keyword)
            except _TrydanKeywordUnavailable:
                _LOGGER.debug("Read endpoint for %s is not available", keyword)
                self._unavailable_realtime_data_keywords.add(keyword)
                self._realtime_data_missing_keywords.discard(keyword)

        return data

    async def get_data(self) -> TrydanData:
        """Get data from Trydan."""
        try:
            data = await self._json_request(f"http://{self._host}/RealTimeData")
            raw_data = self.raw_data
            data = await self._with_missing_realtime_data_keywords(data)
            self.raw_data = raw_data
        except (ConnectTimeout, httpx.ConnectTimeout) as err:
            raise TrydanRetryLater("Timeout connecting to Trydan") from err
        except httpx.ReadTimeout as err:
            raise TrydanRetryLater("Timeout reading from Trydan") from err

        self._data = TrydanData.from_api(data)
        return self._data

    async def set_keyword(
        self,
        keyword: str,
        value: KeywordValue,
    ) -> None:
        """Set a keyword in Trydan."""
        if keyword not in KEYWORDS:
            raise TrydanInvalidKeyword(f"Keyword {keyword} is not valid")

        if keyword in VALIDATION:
            if not VALIDATION[keyword](value):
                raise TrydanInvalidValue(
                    f"Value {value} is not valid for keyword {keyword}"
                )

        serialized_value = _serialize_keyword_value(value)
        url = f"http://{self._host}/write/{keyword}={serialized_value}"
        _LOGGER.debug("HTTP GET: %s", url)
        try:
            data = await self._request(url)
        except ConnectTimeout as err:
            raise TrydanRetryLater("Timeout connecting to Trydan") from err

        if data.status_code != 200 or data.content != b"OK":
            raise TrydanInvalidValue(
                f"Failed for {keyword}={serialized_value}"
                f" code={data.status_code} : <{data.content!r}>"
            )

    @property
    def data(self) -> TrydanData | None:
        """Return cached version of Trydan EVSE."""
        if self._data is None:
            raise TrydanRetryLater("no initial data retrieved")
        return self._data

    @property
    def host(self) -> str:
        """Return the Trydan host."""
        return self._host

    @property
    def id(self) -> str | None:
        """Return the Trydan ID."""
        if self._data is None:
            raise TrydanRetryLater("No data available")
        return self._data.ID

    @property
    def firmware_version(self) -> str | None:
        """Return the Trydan firmware version."""
        if self._data is None:
            raise TrydanRetryLater("No data available")
        return self._data.firmware_version

    @property
    def connected(self) -> bool:
        """Return the Trydan connection state."""
        if self._data is None:
            raise TrydanRetryLater("No data available")
        return self._data.charge_state != ChargeState.NOT_CONNECTED

    @property
    def charging(self) -> bool:
        """Return the Trydan charging state."""
        if self._data is None:
            raise TrydanRetryLater("No data available")
        return self._data.charge_state == ChargeState.CONNECTED_CHARGING

    @property
    def ready(self) -> bool:
        """Return the Trydan ready state."""
        if self._data is None:
            raise TrydanRetryLater("No data available")
        return self._data.ready_state == ReadyState.READY

    async def pause(self, value: bool = True) -> None:
        """Pause state of current charging session."""
        await self.set_keyword(
            "Paused", PauseState.PAUSED if value else PauseState.NOT_PAUSED
        )

    async def resume(self) -> None:
        """Resume state of current charging session."""
        await self.pause(False)

    async def lock(self, value: bool = True) -> None:
        """Disabling state of Charge Point."""
        await self.set_keyword(
            "Locked", LockState.ENABLED if value else LockState.DISABLED
        )

    async def unlock(self) -> None:
        """Disabling state of Charge Point."""
        await self.lock(False)

    async def timer(self, value: bool = True) -> None:
        """Set the Charge Point Timer state."""
        await self.set_keyword(
            "Timer",
            ChargePointTimerState.TIMER_ON
            if value
            else ChargePointTimerState.TIMER_OFF,
        )

    async def timer_disable(self) -> None:
        """Disable the Charge Point Timer."""
        await self.timer(False)

    async def intensity(self, current: int) -> None:
        """Set the intensity of the Charge Point."""
        if not 6 <= current <= 32:
            raise TrydanInvalidValue("Intensity must be between 6 and 32")

        await self.set_keyword("Intensity", current)

    async def voltage_installation(self, voltage: int) -> None:
        """Set the installation voltage."""
        if not (voltage > 0):
            raise TrydanInvalidValue("Installation Voltage must be positive")

        await self.set_keyword("VoltageInstallation", voltage)

    async def charge_mode(self, mode: ChargeMode) -> None:
        """Set the Charge Mode."""
        await self.set_keyword("ChargeMode", mode)

    async def light_led(self, intensity: int) -> None:
        """Set the Light LED intensity."""
        if not (intensity >= 0 and intensity <= 100):
            raise TrydanInvalidValue("LED intensity must be between 0 and 100")

        await self.set_keyword("LightLED", intensity)

    async def logo_led(self, intensity: int) -> None:
        """Set the Logo LED intensity."""
        if not (intensity >= 0 and intensity <= 100):
            raise TrydanInvalidValue("LED intensity must be between 0 and 100")

        await self.set_keyword("LogoLED", intensity)

    async def dynamic(self, value: bool = True) -> None:
        """Set the Dynamic Intensity Modulation state."""
        await self.set_keyword(
            "Dynamic", DynamicState.ENABLED if value else DynamicState.DISABLED
        )

    async def dynamic_disable(self) -> None:
        """Disable the Dynamic Intensity Modulation."""
        await self.dynamic(False)

    async def min_intensity(self, current: int) -> None:
        """Set the minimum intensity of the Charge Point."""
        if not 6 <= current <= 32:
            raise TrydanInvalidValue("Intensity must be between 6 and 32")

        await self.set_keyword("MinIntensity", current)

    async def max_intensity(self, current: int) -> None:
        """Set the maximum intensity of the Charge Point."""
        if not 6 <= current <= 32:
            raise TrydanInvalidValue("Intensity must be between 6 and 32")

        await self.set_keyword("MaxIntensity", current)

    async def pause_dynamic(self, value: bool = True) -> None:
        """Set the Pause Dynamic state."""
        await self.set_keyword(
            "PauseDynamic",
            PauseDynamicState.NOT_MODULATING if value else PauseDynamicState.MODULATING,
        )

    async def resume_dynamic(self) -> None:
        """Resume the Pause Dynamic state."""
        await self.pause_dynamic(False)

    async def dynamic_power_mode(self, mode: DynamicPowerMode) -> None:
        """Set the Dynamic Power Mode."""
        await self.set_keyword("DynamicPowerMode", mode)

    async def contracted_power(self, power: int) -> None:
        """Set the Contracted Power."""
        if self.data is None:
            raise TrydanRetryLater("No data available")
        if (
            self.data.dynamic_power_mode
            not in (
                DynamicPowerMode.TIMED_POWER_ENABLED,
                DynamicPowerMode.TIMED_POWER_DISABLED_AND_FV_EXCL_MODE_SETTED,
            )
            and power < 0
        ):
            raise TrydanInvalidValue("Contracted Power must be positive")
        await self.set_keyword("ContractedPower", power)
