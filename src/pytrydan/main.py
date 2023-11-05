from rich import print

from .trydan import Trydan


async def trydan_status(ip: str) -> int:
    """Retrieve Trydan Status."""
    trydan = Trydan(ip)
    data = await trydan.get_data()

    print(data)

    return 0


async def trydan_set(ip: str, keyword: str, value: str) -> int:
    """Set KeyWord value in Trydan."""
    trydan = Trydan(ip)
    await trydan.set_keyword(keyword, value)

    return 0
