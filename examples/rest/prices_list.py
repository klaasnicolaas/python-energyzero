"""Asynchronous example: list electricity and gas prices via REST API."""

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from energyzero import EnergyZero, TimeRange  # pyright: ignore[reportMissingImports]


def _format_entry(entry: dict[str, float | TimeRange]) -> str:
    timerange = entry["timerange"]
    price = entry["price"]

    if not isinstance(timerange, TimeRange) or not isinstance(price, float):
        msg = "Entry does not contain a valid timerange/price pair"
        raise TypeError(msg)

    return f"{timerange}: €{price:0.3f}"


async def main() -> None:
    """Fetch and print electricity and gas price lists for a single day."""
    async with EnergyZero() as client:
        local_tz = ZoneInfo("Europe/Amsterdam")
        today = datetime.now(local_tz).date()
        electricity = await client.get_electricity_prices(
            start_date=today,
            local_tz=local_tz,
        )
        gas = await client.get_gas_prices(
            start_date=today,
            local_tz=local_tz,
        )

    print(f"--- ELECTRICITY ({today.isoformat()}) ---")
    print("\n".join(_format_entry(entry) for entry in electricity.timestamp_prices))

    print(f"\n--- GAS ({today.isoformat()}) ---")
    print("\n".join(_format_entry(entry) for entry in gas.timestamp_prices))


if __name__ == "__main__":
    asyncio.run(main())
