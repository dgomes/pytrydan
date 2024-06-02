import logging
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

VALIDATION = {
    "ChargeState": lambda x: x in ChargePointTimerState,
    "DynamicPowerMode": lambda x: x in DynamicPowerMode,
    "Dynamic": lambda x: x in DynamicState,
    "Locked": lambda x: x in LockState,
    "PauseDynamic": lambda x: x in PauseDynamicState,
    "Paused": lambda x: x in PauseState,
    "Intensity": lambda x: x >= 6 and x <= 32,
    "MinIntensity": lambda x: x >= 6 and x <= 32,
    "MaxIntensity": lambda x: x >= 6 and x <= 32,
}

_LOGGER = logging.getLogger(__name__)


class Trydan:
    """Class for communicating with Trydan."""

    def __init__(
        self,
        host: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize."""
        self._host = host
        self._client = client or httpx.AsyncClient()
        self._timeout = API_TIMEOUT
        self._data: TrydanData | None = None

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

    async def _json_request(self, end_point: str) -> Any:
        """Make a request to Trydan and return the JSON response."""
        response = await self._request(end_point)
        try:
            return orjson.loads(response.content)
        except orjson.JSONDecodeError as err:
            _LOGGER.error(
                "Error decoding JSON response from Trydan: ", response.content
            )
            raise TrydanInvalidResponse(
                "Error decoding JSON response from Trydan"
            ) from err

    async def get_data(self) -> TrydanData:
        """Get data from Trydan."""
        try:
            data = await self._json_request(f"http://{self._host}/RealTimeData")
        except ConnectTimeout as err:
            raise TrydanRetryLater("Timeout connecting to Trydan") from err
        except httpx.ReadTimeout as err:
            raise TrydanRetryLater("Timeout reading from Trydan") from err

        self._data = TrydanData.from_api(data)
        return self._data

    async def set_keyword(
        self,
        keyword: str,
        value: str
        | int
        | ChargePointTimerState
        | DynamicPowerMode
        | DynamicState
        | LockState
        | PauseDynamicState
        | PauseState
        | TrydanData,
    ) -> None:
        """Set a keyword in Trydan."""
        if keyword not in KEYWORDS:
            raise TrydanInvalidKeyword(f"Keyword {keyword} is not valid")

        if keyword in VALIDATION:
            if not VALIDATION[keyword](value):
                raise TrydanInvalidValue(
                    f"Value {value} is not valid for keyword {keyword}"
                )

        url = f"http://{self._host}/write/{keyword}={value}"
        _LOGGER.debug("HTTP GET: %s", url)
        try:
            data = await self._request(url)
        except ConnectTimeout as err:
            raise TrydanRetryLater("Timeout connecting to Trydan") from err

        if data.status_code != 200 or data.content != b"OK":
            raise TrydanInvalidValue(
                f"Failed for {keyword}={value}"
                " code={data.status_code} : <{data.content}>"
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
        if not (current >= 6 and current <= 32):
            raise TrydanInvalidValue("Intensity must be between 6 and 32")

        await self.set_keyword("Intensity", current)

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
        if not (current >= 6 and current <= 32):
            raise TrydanInvalidValue("Intensity must be between 6 and 32")

        await self.set_keyword("MinIntensity", current)

    async def max_intensity(self, current: int) -> None:
        """Set the maximum intensity of the Charge Point."""
        if not (current >= 6 and current <= 32):
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
        if not (power > 0):
            raise TrydanInvalidValue("Contracted Power must be positive")
        await self.set_keyword("ContractedPower", power)
