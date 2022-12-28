"""Asynchronous Python client for the EnergyZero API."""

import asyncio
from datetime import date, timedelta

import pytz

from energyzero import EnergyZero


async def main() -> None:
    """Show example on fetching the energy prices from EnergyZero."""
    async with EnergyZero() as client:
        local = pytz.timezone("Europe/Amsterdam")
        today = date(2022, 12, 14)
        tomorrow = date(2022, 12, 15)

        # Select your test readings
        energy_reading: bool = True
        gas_reading: bool = True

        if energy_reading:
            energy_today = await client.energy_prices(start_date=today, end_date=today)
            energy_tomorrow = await client.energy_prices(
                start_date=tomorrow, end_date=tomorrow
            )

            print("--- ENERGY TODAY ---")
            print(f"Max price: {energy_today.extreme_prices[1]}")
            print(f"Min price: {energy_today.extreme_prices[0]}")
            print(f"Average price: {energy_today.average_price}")
            print(f"Percentage: {energy_today.pct_of_max_price}")
            print()
            print(
                f"High price time: {energy_today.highest_price_time.astimezone(local)}"
            )
            print(
                f"Lowest price time: {energy_today.lowest_price_time.astimezone(local)}"
            )
            print()
            print(f"Current hourprice: {energy_today.current_price}")
            next_hour = energy_today.utcnow() + timedelta(hours=1)
            print(f"Next hourprice: {energy_today.price_at_time(next_hour)}")

            print()
            print("--- ENERGY TOMORROW ---")
            print(f"Max price: {energy_tomorrow.extreme_prices[1]}")
            print(f"Min price: {energy_tomorrow.extreme_prices[0]}")
            print(f"Average price: {energy_tomorrow.average_price}")
            print()
            time_high = energy_tomorrow.highest_price_time.astimezone(local)
            print(f"Highest price time: {time_high}")
            time_low = energy_tomorrow.lowest_price_time.astimezone(local)
            print(f"Lowest price time: {time_low}")

        if gas_reading:
            gas_today = await client.gas_prices(start_date=today, end_date=today)
            print()
            print("--- GAS TODAY ---")
            print(f"Max price: {gas_today.extreme_prices[1]}")
            print(f"Min price: {gas_today.extreme_prices[0]}")
            print(f"Average price: {gas_today.average_price}")
            print()
            print(f"Current price: {gas_today.current_price}")
            next_hour = gas_today.utcnow() + timedelta(hours=1)
            print(f"Next price: {gas_today.price_at_time(next_hour)}")


if __name__ == "__main__":
    asyncio.run(main())
