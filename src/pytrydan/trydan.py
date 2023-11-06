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
from .models.trydan import TrydanData

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

        status_code = response.status_code
        if status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
            raise TrydanCommunicationError(
                f"Failed for {url} with status {status_code}"
            )

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
        self._data = TrydanData.from_api(data)
        return self._data

    async def set_keyword(self, keyword: str, value: str) -> None:
        """Set a keyword in Trydan."""
        if keyword not in KEYWORDS:
            raise TrydanInvalidKeyword(f"Keyword {keyword} is not valid")

        # TODO: Check if value is valid based on keyword used
        data = await self._request(f"http://{self._host}/write/{keyword}={value}")

        if data.status_code != 200 or data.content != b"OK":
            raise TrydanInvalidValue(
                f"Failed for {keyword}={value} with status {data.status_code}"
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
    def firmware_version(self) -> str | None:
        """Return the Trydan firmware version."""
        if self._data is None:
            raise TrydanRetryLater("No data available")
        return self._data.firmware_version
