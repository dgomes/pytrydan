from rich import print

from .trydan import Trydan


async def trydan_status(ip: str) -> int:
    """Retrieve Trydan Status."""
    trydan = Trydan(ip)
    data = await trydan.get_data()

    print(data)

    return 0


async def trydan_connected(ip: str) -> int:
    """Retrieve Trydan Status."""
    trydan = Trydan(ip)
    await trydan.get_data()

    print(trydan.connected)

    return 0


async def trydan_charging(ip: str) -> int:
    """Retrieve Trydan Status."""
    trydan = Trydan(ip)
    await trydan.get_data()

    print(trydan.charging)

    return 0


async def trydan_ready(ip: str) -> int:
    """Retrieve Trydan Status."""
    trydan = Trydan(ip)
    await trydan.get_data()

    print(trydan.ready)

    return 0


async def trydan_set(ip: str, keyword: str, value: str) -> int:
    """Set KeyWord value in Trydan."""
    trydan = Trydan(ip)
    try:
        await trydan.set_keyword(keyword, value)
    except Exception as e:
        print(e)
        return 1
    return 0


async def trydan_pause(ip: str) -> int:
    """Pause Trydan."""
    trydan = Trydan(ip)
    try:
        await trydan.pause()
    except Exception as e:
        print(e)
        return 1
    return 0


async def trydan_resume(ip: str) -> int:
    """Resume Trydan."""
    trydan = Trydan(ip)
    try:
        await trydan.resume()
    except Exception as e:
        print(e)
        return 1
    return 0


async def trydan_lock(ip: str) -> int:
    """Lock Trydan."""
    trydan = Trydan(ip)
    try:
        await trydan.lock()
    except Exception as e:
        print(e)
        return 1

    return 0


async def trydan_unlock(ip: str) -> int:
    """Unlock Trydan."""
    trydan = Trydan(ip)
    try:
        await trydan.unlock()
    except Exception as e:
        print(e)
        return 1
    return 0


async def trydan_intensity(ip: str, intensity: int) -> int:
    """Set Intensity in Trydan."""
    trydan = Trydan(ip)
    try:
        await trydan.intensity(intensity)
    except Exception as e:
        print(e)
        return 1

    return 0
