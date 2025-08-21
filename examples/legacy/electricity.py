"""Asynchronous Python client for the EnergyZero API (legacy electricity prices)."""

import asyncio
from datetime import date, timedelta, tzinfo

import pytz

from energyzero import Electricity, EnergyZero, VatOption


def _price_to_string(price: float | None) -> str:
    if price is None:
        return "Unknown"
    return f"€{price:.2f} (€{price})"


def _print_energy_price_info(prices: Electricity, tz: tzinfo) -> None:
    if not prices.prices:
        print("No data available")
        return

    print(f"Max price: {_price_to_string(prices.extreme_prices[1])}")
    print(f"Min price: {_price_to_string(prices.extreme_prices[0])}")
    print(f"Average price: {_price_to_string(prices.average_price)}")

    if prices.pct_of_max_price is not None:
        print(f"Percentage: {prices.pct_of_max_price}%")

    if prices.highest_price_time:
        print(f"High time: {prices.highest_price_time.astimezone(tz)}")

    if prices.lowest_price_time:
        print(f"Lowest time: {prices.lowest_price_time.astimezone(tz)}")

    if prices.current_price is not None:
        print(f"Current hourprice: {_price_to_string(prices.current_price)}")

        next_hour = prices.utcnow() + timedelta(hours=1)
        next_price = prices.price_at_time(next_hour)
        print(f"Next hourprice: {_price_to_string(next_price)}")

        if prices.hours_priced_equal_or_lower is not None:
            print(
                "Hours lower or equal than current "
                f"price: {prices.hours_priced_equal_or_lower}"
            )


async def main() -> None:
    """Show example on fetching the electricity prices (legacy) from EnergyZero."""
    async with EnergyZero() as client:
        tz = pytz.timezone("Europe/Amsterdam")
        today = date(2025, 6, 23)
        tomorrow = date(2025, 6, 24)

        print("--- ENERGY TODAY ---")
        energy_today = await client.get_electricity_prices_legacy(
            start_date=today, end_date=today, vat=VatOption.EXCLUDE
        )
        _print_energy_price_info(energy_today, tz)

        print("\n--- ENERGY TOMORROW ---")
        energy_tomorrow = await client.get_electricity_prices_legacy(
            start_date=tomorrow, end_date=tomorrow, vat=VatOption.EXCLUDE
        )
        _print_energy_price_info(energy_tomorrow, tz)


if __name__ == "__main__":
    asyncio.run(main())
