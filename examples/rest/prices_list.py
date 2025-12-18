"""Asynchronous example: list electricity and gas prices via REST API."""

import asyncio
from datetime import UTC, datetime

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
        today = datetime.now(UTC).astimezone().date()
        electricity = await client.get_electricity_prices(start_date=today)
        gas = await client.get_gas_prices(start_date=today)

    print(f"--- ELECTRICITY ({today.isoformat()}) ---")
    print("\n".join(_format_entry(entry) for entry in electricity.timestamp_prices))

    print(f"\n--- GAS ({today.isoformat()}) ---")
    print("\n".join(_format_entry(entry) for entry in gas.timestamp_prices))


if __name__ == "__main__":
    asyncio.run(main())
