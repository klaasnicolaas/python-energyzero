"""Asynchronous Python client for the EnergyZero API."""

import asyncio
from datetime import date, timedelta

import pytz

from energyzero import EnergyZero


async def main() -> None:
    """Show example on fetching the energy prices from EnergyZero."""
    async with EnergyZero() as client:
        local = pytz.timezone("CET")
        today = date(2023, 3, 29)
        tomorrow = date(2023, 3, 29)

        energy_today = await client.energy_prices(start_date=today, end_date=today)
        energy_tomorrow = await client.energy_prices(
            start_date=tomorrow,
            end_date=tomorrow,
        )

        print("--- ENERGY TODAY ---")
        print(f"Max price: {energy_today.extreme_prices[1]}")
        print(f"Min price: {energy_today.extreme_prices[0]}")
        print(f"Average price: {energy_today.average_price}")
        print(f"Percentage: {energy_today.pct_of_max_price}")
        print()
        print(
            f"High time: {energy_today.highest_price_time.astimezone(local)}",
        )
        print(
            f"Lowest time: {energy_today.lowest_price_time.astimezone(local)}",
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


if __name__ == "__main__":
    asyncio.run(main())
