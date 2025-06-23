"""Asynchronous example: electricity prices via GraphQL."""

import asyncio
from datetime import datetime, timedelta

import pytz

from energyzero import EnergyPrices, EnergyZero


def _price_to_string(price: float | None) -> str:
    if price is None:
        return "Unknown"
    return f"€{price:0.2f} (€{price})"


def _print_energy_price_info(energy_prices: EnergyPrices) -> None:
    local_tz = pytz.timezone("Europe/Amsterdam")

    if len(energy_prices.prices) == 0:
        print("No data available")
        return

    today_extreme_prices = energy_prices.extreme_prices
    next_hour = energy_prices.utcnow() + timedelta(hours=1)
    current_price = energy_prices.current_price
    next_hour_price = energy_prices.price_at_time(next_hour)
    today_highest_price_time_range = energy_prices.highest_price_time_range
    today_lowest_price_time_range = energy_prices.lowest_price_time_range

    if today_extreme_prices is not None:
        print(f"Max price: {_price_to_string(today_extreme_prices[1])}")
        print(f"Min price: {_price_to_string(today_extreme_prices[0])}")

    print(f"Average price: {_price_to_string(energy_prices.average_price)}")

    if current_price is not None:
        print(f"Percentage: {energy_prices.pct_of_max_price}%")

    if today_highest_price_time_range is not None:
        print(f"High time: {today_highest_price_time_range.astimezone(local_tz)}")

    if today_lowest_price_time_range is not None:
        print(f"Lowest time: {today_lowest_price_time_range.astimezone(local_tz)}")

    if current_price is not None:
        print(f"Current hourprice: {_price_to_string(current_price)}")

    if next_hour_price is not None:
        print(f"Next hourprice: {_price_to_string(next_hour_price)}")

    best_hours = energy_prices.time_ranges_priced_equal_or_lower

    if best_hours is not None and best_hours > 0:
        print(f"Hours lower or equal than current price: {best_hours}")


async def main() -> None:
    """Show example on fetching the electricity prices from EnergyZero."""
    async with EnergyZero() as client:
        local_tz = pytz.timezone("Europe/Amsterdam")
        today = datetime.now(local_tz).date()
        tomorrow = today + timedelta(days=1)

        energy_today = await client.get_electricity_prices(
            start_date=today, end_date=today
        )
        energy_tomorrow = await client.get_electricity_prices(
            start_date=tomorrow, end_date=tomorrow
        )

        print("--- ENERGY TODAY ---")
        _print_energy_price_info(energy_today)

        print("\n--- ENERGY TOMORROW ---")
        _print_energy_price_info(energy_tomorrow)


if __name__ == "__main__":
    asyncio.run(main())
