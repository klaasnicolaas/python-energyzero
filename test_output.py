"""Asynchronous Python client for the EnergyZero API."""

import asyncio
from datetime import datetime

import pytz

from energyzero import EnergyZero


async def main() -> None:
    """Show example on fetching the energy prices from EnergyZero."""
    async with EnergyZero() as client:
        local = pytz.timezone("Europe/Amsterdam")
        today = datetime.strptime("2022-12-09", "%Y-%m-%d")
        tomorrow = datetime.strptime("2022-12-10", "%Y-%m-%d")

        # Select your test readings
        energy_reading: bool = True
        gas_reading: bool = False

        if energy_reading:
            energy_today = await client.energy_prices(start_date=today, end_date=today)
            energy_tomorrow = await client.energy_prices(
                start_date=tomorrow, end_date=tomorrow
            )

            print(energy_today)
            print(energy_tomorrow)

            print("--- TODAY ---")
            print(f"Max price: {energy_today.max_price}")
            print(f"Min price: {energy_today.min_price}")
            print(f"Average price: {energy_today.average_price}")
            print()
            print(
                f"High price time: {energy_today.highest_price_time.astimezone(local)}"
            )
            print(
                f"Lowest price time: {energy_today.lowest_price_time.astimezone(local)}"
            )
            print()
            print(f"Current hourprice: {energy_today.current_hourprice}")
            print(f"Next hourprice: {energy_today.next_hourprice}")

            print()
            print("--- TOMORROW ---")
            print(f"Max price: {energy_tomorrow.max_price}")
            print(f"Min price: {energy_tomorrow.min_price}")
            print(f"Average price: {energy_tomorrow.average_price}")
            print()
            time_high = energy_tomorrow.highest_price_time.astimezone(local)
            print(f"Highest price time: {time_high}")
            time_low = energy_tomorrow.lowest_price_time.astimezone(local)
            print(f"Lowest price time: {time_low}")

        if gas_reading:
            gas_today = await client.gas_prices(start_date=today, end_date=today)

            print("--- TODAY ---")
            print(f"Max price: {gas_today.max_price}")
            print(f"Min price: {gas_today.min_price}")
            print(f"Average price: {gas_today.average_price}")
            print()
            print(f"Current hourprice: {gas_today.current_hourprice}")
            print(f"Next hourprice: {gas_today.next_hourprice}")


if __name__ == "__main__":
    asyncio.run(main())
