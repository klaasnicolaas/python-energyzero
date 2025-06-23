"""Asynchronous Python client for the EnergyZero API."""

import asyncio
from datetime import date, timedelta

from energyzero import EnergyZero, VatOption


async def main() -> None:
    """Show example on fetching the gas prices from EnergyZero."""
    async with EnergyZero(vat=VatOption.INCLUDE) as client:
        today = date(2025, 6, 3)

        gas_today = await client.get_gas_prices_legacy(start_date=today, end_date=today)
        print()
        print("--- GAS TODAY ---")
        print(f"Max price: €{gas_today.extreme_prices[1]}")
        print(f"Min price: €{gas_today.extreme_prices[0]}")
        print(f"Average price: €{gas_today.average_price}")
        print()
        print(f"Current price: €{gas_today.current_price}")
        next_hour = gas_today.utcnow() + timedelta(hours=1)
        print(f"Next price: €{gas_today.price_at_time(next_hour)}")


if __name__ == "__main__":
    asyncio.run(main())
