"""Asynchronous Python client for the EnergyZero API."""

import asyncio
from datetime import UTC, datetime, timedelta
from os import environ
from time import tzset

from energyzero import EnergyPrices, EnergyZero


def _price_to_string(price: float | None) -> str:
    if price is None:
        return "Unknown"

    return f"€{price:0.2f} (€{price})"


def _print_energy_price_info(energy_prices: EnergyPrices) -> None:
    local_tz = datetime.now(UTC).astimezone().tzinfo

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

    best_hours = energy_prices.hours_priced_equal_or_lower

    if best_hours is not None and best_hours > 0:
        print(f"Hours lower or equal than current price: {best_hours}")


async def main() -> None:
    """Show example on fetching the gas prices from EnergyZero."""
    async with EnergyZero() as client:
        # Note: The devcontainer's timezone is always UTC
        # Simulate a call from a client running in the Netherlands
        environ["TZ"] = "Europe/Amsterdam"
        tzset()

        local_tz = datetime.now(UTC).astimezone().tzinfo
        today = datetime.now(tz=local_tz).date()
        tomorrow = today + timedelta(days=1)

        energy_today = await client.gas_prices_ex(start_date=today, end_date=today)
        energy_tomorrow = await client.gas_prices_ex(
            start_date=tomorrow, end_date=tomorrow
        )

        print("--- GAS TODAY ---")

        _print_energy_price_info(energy_today)

        # Note: tomorrow's prices will be known after 15:00 today,
        # if you run this sample before 15:00, no data for tomorrow
        # will be available.

        print()
        print("--- GAS TOMORROW ---")

        _print_energy_price_info(energy_tomorrow)


if __name__ == "__main__":
    asyncio.run(main())
