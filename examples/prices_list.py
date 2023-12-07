"""Asynchronous Python client for the EnergyZero API."""

import asyncio
from datetime import date

from energyzero import EnergyZero, VatOption


async def main() -> None:
    """Show example on fetching the timestamp lists from EnergyZero."""
    async with EnergyZero(vat=VatOption.INCLUDE) as client:
        today = date(2023, 12, 5)
        energy = await client.energy_prices(start_date=today, end_date=today)
        gas = await client.gas_prices(start_date=today, end_date=today)

        print("--- ENERGY ---")
        print(energy.timestamp_prices)
        print()

        print("--- GAS ---")
        print(gas.timestamp_prices)


if __name__ == "__main__":
    asyncio.run(main())
