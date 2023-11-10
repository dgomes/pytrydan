import asyncio
from ipaddress import ip_address

import typer
from rich import print

from .main import (
    trydan_charging,
    trydan_connected,
    trydan_intensity,
    trydan_lock,
    trydan_pause,
    trydan_ready,
    trydan_resume,
    trydan_set,
    trydan_status,
    trydan_unlock,
)

app = typer.Typer()


@app.command()
def status(ip: str) -> None:
    """Retrieve Trydan Status."""
    print("Connecting to %s", ip_address(ip))

    asyncio.run(trydan_status(ip))


@app.command()
def connected(ip: str) -> None:
    """Retrieve Trydan Status."""
    print("Connecting to %s", ip_address(ip))

    asyncio.run(trydan_connected(ip))


@app.command()
def charging(ip: str) -> None:
    """Retrieve Trydan Status."""
    print("Connecting to %s", ip_address(ip))

    asyncio.run(trydan_charging(ip))


@app.command()
def ready(ip: str) -> None:
    """Retrieve Trydan Status."""
    print("Connecting to %s", ip_address(ip))

    asyncio.run(trydan_ready(ip))


@app.command()
def pause(ip: str) -> None:
    """Pause Trydan EVSE."""
    print("Connecting to %s", ip_address(ip))

    asyncio.run(trydan_pause(ip))


@app.command()
def resume(ip: str) -> None:
    """Resume Trydan EVSE."""
    print("Connecting to %s", ip_address(ip))

    asyncio.run(trydan_resume(ip))


@app.command()
def lock(ip: str) -> None:
    """Lock Trydan EVSE."""
    print("Connecting to %s", ip_address(ip))

    asyncio.run(trydan_lock(ip))


@app.command()
def unlock(ip: str) -> None:
    """Unlock Trydan EVSE."""
    print("Connecting to %s", ip_address(ip))

    asyncio.run(trydan_unlock(ip))


@app.command()
def intensity(ip: str, intensity: int) -> None:
    """Set Intensity in Trydan EVSE."""
    print("Connecting to %s", ip_address(ip))

    asyncio.run(trydan_intensity(ip, intensity))


@app.command()
def set(ip: str, keyword: str, value: str) -> None:
    """Set KeyWord value in Trydan."""
    print("Connecting to %s", ip_address(ip))

    asyncio.run(trydan_set(ip, keyword, value))
