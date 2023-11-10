import pytest
import respx
from httpx import Response

from pytrydan.exceptions import (
    TrydanCommunicationError,
    TrydanInvalidResponse,
)

from .conftest import _get_mock_trydan, _load_json_fixture


@pytest.mark.asyncio
@respx.mock
async def test_bad_status():
    respx.get("/RealTimeData").mock(return_value=Response(404, json={}))

    envoy = await _get_mock_trydan()
    with pytest.raises(TrydanInvalidResponse):
        data = await envoy.get_data()
        assert data is None

    respx.get("/RealTimeData").mock(return_value=Response(403, json={}))

    envoy = await _get_mock_trydan()
    with pytest.raises(TrydanCommunicationError):
        data = await envoy.get_data()
        assert data is None


@pytest.mark.asyncio
@respx.mock
async def test_status():
    respx.get("/RealTimeData").mock(
        return_value=Response(200, json=_load_json_fixture("RealTimeData"))
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


@pytest.mark.asyncio
@respx.mock
async def test_status_charging():
    respx.get("/RealTimeData").mock(
        return_value=Response(200, json=_load_json_fixture("RealTimeData_Charging"))
    )

    envoy = await _get_mock_trydan()
    data = await envoy.get_data()
    assert data is not None

    assert data.charge_state == 2
    assert data.ready_state == 0
    assert data.charge_power == 2664
    assert data.charge_energy == 0.07
    assert data.slave_error == 0
    assert data.charge_time == 105
    assert data.house_power == 0
    assert data.fv_power == 0
    assert data.paused == 0
    assert data.locked == 0
    assert data.timer == 1
    assert data.intensity == 12
    assert data.dynamic == 0
    assert data.min_intensity == 6
    assert data.max_intensity == 16
    assert data.pause_dynamic == 0
    assert data.firmware_version == "1.6.18"
    assert data.dynamic_power_mode == 2
    assert data.contracted_power == 4600
