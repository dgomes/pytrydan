"""Tests for the pytrydan data models."""

from pytrydan.models.trydan import SlaveCommunicationState, TrydanData

from .conftest import _load_json_fixture


def test_slave_error_unmapped_code_falls_back_to_undefined_error():
    """Undocumented SlaveError codes must not raise ValueError."""
    assert SlaveCommunicationState(224) is SlaveCommunicationState.UNDEFINED_ERROR


def test_slave_error_known_codes_still_map():
    """Documented SlaveError codes keep their meaning."""
    assert SlaveCommunicationState(0) is SlaveCommunicationState.NO_ERROR
    assert SlaveCommunicationState(1) is SlaveCommunicationState.COMMUNICATION
    assert SlaveCommunicationState(254) is (
        SlaveCommunicationState.IP_CONNECTION_FAILED
    )


def test_from_api_with_unmapped_slave_error():
    """Parsing RealTimeData with SlaveError 224 works (firmware v2.5.1)."""
    data = _load_json_fixture("RealTimeData")
    data["SlaveError"] = 224

    trydan_data = TrydanData.from_api(data)

    assert trydan_data.slave_error is SlaveCommunicationState.UNDEFINED_ERROR
