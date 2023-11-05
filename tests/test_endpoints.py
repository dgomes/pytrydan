from pathlib import Path
from typing import Any

import orjson
import pytest
import respx
from httpx import Response

from pytrydan import Trydan


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> str:
    with open(_fixtures_dir() / name) as read_in:
        return read_in.read()


def _load_json_fixture() -> dict[str, Any]:
    return orjson.loads(_load_fixture("RealTimeData"))


async def _get_mock_trydan(update: bool = True):  # type: ignore[no-untyped-def]
    """Return a mock Trydan."""
    trydan = Trydan("127.0.0.1")
    return trydan


@pytest.mark.asyncio
@respx.mock
async def test_status():
    respx.get("/RealTimeData").mock(
        return_value=Response(200, json=_load_json_fixture())
    )

    envoy = await _get_mock_trydan()
    data = await envoy.get_data()
    assert data is not None

    assert data.charge_state == 1
    assert data.ready_state == 1
    assert data.charge_power == 0
    assert data.charge_energy == 7.6
    assert data.slave_error == 0
    assert data.charge_time == 9979
    assert data.house_power == 0
    assert data.fv_power == 0
    assert data.paused == 0
    assert data.locked == 0
    assert data.timer == 1
    assert data.intensity == 16
    assert data.dynamic == 0
    assert data.min_intensity == 6
    assert data.max_intensity == 16
    assert data.pause_dynamic == 0
    assert data.firmware_version == "1.6.18"
    assert data.dynamic_power_mode == 2
    assert data.contracted_power == 4600
