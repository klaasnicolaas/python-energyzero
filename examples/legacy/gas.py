"""Asynchronous Python client for the EnergyZero API (Legacy gas prices)."""

import asyncio
from datetime import datetime, timedelta

import pytz

from energyzero import EnergyZero


def _price_to_string(price: float | None) -> str:
    if price is None:
        return "Unknown"
    return f"€{price:.2f} (€{price})"


async def main() -> None:
    """Show example on fetching the legacy gas prices from EnergyZero."""
    async with EnergyZero() as client:
        tz = pytz.timezone("Europe/Amsterdam")
        today = datetime.now(tz).date()

        gas_today = await client.get_gas_prices_legacy(start_date=today, end_date=today)

        print("--- GAS TODAY ---")
        print(f"Max price: {_price_to_string(gas_today.extreme_prices[1])}")
        print(f"Min price: {_price_to_string(gas_today.extreme_prices[0])}")
        print(f"Average price: {_price_to_string(gas_today.average_price)}")

        if gas_today.current_price is not None:
            print(f"Current price: {_price_to_string(gas_today.current_price)}")

            next_hour = gas_today.utcnow() + timedelta(hours=1)
            next_price = gas_today.price_at_time(next_hour)
            print(f"Next price: {_price_to_string(next_price)}")


if __name__ == "__main__":
    asyncio.run(main())
