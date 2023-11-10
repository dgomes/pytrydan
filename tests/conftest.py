from pathlib import Path
from typing import Any

import orjson

from pytrydan import Trydan


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> str:
    with open(_fixtures_dir() / name) as read_in:
        return read_in.read()


def _load_json_fixture(case_endpoint: str) -> dict[str, Any]:
    return orjson.loads(_load_fixture(case_endpoint))


async def _get_mock_trydan(update: bool = True):  # type: ignore[no-untyped-def]
    """Return a mock Trydan."""
    trydan = Trydan("127.0.0.1")
    return trydan
