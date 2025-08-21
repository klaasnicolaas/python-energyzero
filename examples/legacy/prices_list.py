"""Asynchronous Python client for the EnergyZero API (legacy example)."""

import asyncio
from datetime import date, datetime, time

import pytz

from energyzero import EnergyZero


def print_timestamp_prices(
    data: list[dict[str, float | datetime]], title: str, tz: pytz.BaseTzInfo
) -> None:
    """Print a list of timestamp prices with timezone conversion."""
    print(f"--- {title.upper()} ---")
    for item in data:
        ts = item.get("timestamp")
        price = item.get("price")

        if not isinstance(price, (float, int)) or ts is None:
            continue

        # Convert to datetime if it's a date (e.g., gas legacy)
        if isinstance(ts, date) and not isinstance(ts, datetime):
            ts = datetime.combine(ts, time.min).replace(tzinfo=pytz.UTC)

        if isinstance(ts, datetime):
            print(f"{ts.astimezone(tz).isoformat()}: €{price:.4f}")
    print()


async def main() -> None:
    """Fetch and print electricity and gas prices (legacy) with timestamp lists."""
    async with EnergyZero() as client:
        today = date(2025, 6, 23)
        tz = pytz.timezone("Europe/Amsterdam")

        electricity = await client.get_electricity_prices_legacy(
            start_date=today, end_date=today
        )
        gas = await client.get_gas_prices_legacy(start_date=today, end_date=today)

        print_timestamp_prices(electricity.timestamp_prices, "electricity", tz)
        print_timestamp_prices(gas.timestamp_prices, "gas", tz)


if __name__ == "__main__":
    asyncio.run(main())
