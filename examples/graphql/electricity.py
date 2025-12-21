"""Asynchronous example: electricity prices via GraphQL."""

import asyncio
from datetime import datetime, timedelta, tzinfo

import pytz

from energyzero import (  # pyright: ignore[reportMissingImports]
    APIBackend,
    EnergyPrices,
    EnergyZero,
)


def _price_to_string(price: float | None) -> str:
    if price is None:
        return "Unknown"
    return f"€{price:0.3f}"


def _print_summary(label: str, data: EnergyPrices, tz: tzinfo) -> None:
    print(f"--- {label} ---")
    if len(data.prices) == 0:
        print("No electricity data available")
        return

    min_price, max_price = data.extreme_prices
    print(f"Average price: {_price_to_string(data.average_price)}")
    print(f"Min price: {_price_to_string(min_price)}")
    print(f"Max price: {_price_to_string(max_price)}")
    print(f"Lowest time: {data.lowest_price_time_range.astimezone(tz)}")
    print(f"Highest time: {data.highest_price_time_range.astimezone(tz)}")

    current = data.current_price
    if current is not None:
        print(f"Current price: {_price_to_string(current)}")
        print(f"Percent of max: {data.pct_of_max_price}%")

    next_hour = data.utcnow() + timedelta(hours=1)
    next_price = data.price_at_time(next_hour)
    if next_price is not None:
        print(f"Next hour price: {_price_to_string(next_price)}")

    print(f"Blocks <= current price: {data.time_ranges_priced_equal_or_lower}")
    print()


async def main() -> None:
    """Fetch hourly electricity prices for today and tomorrow via GraphQL."""
    async with EnergyZero(backend=APIBackend.GRAPHQL) as client:
        local_tz = pytz.timezone("Europe/Amsterdam")
        today = datetime.now(local_tz).date()
        tomorrow = today + timedelta(days=1)

        energy_today = await client.get_electricity_prices(
            start_date=today,
            end_date=today,
        )
        energy_tomorrow = await client.get_electricity_prices(
            start_date=tomorrow,
            end_date=tomorrow,
        )

    _print_summary(f"ELECTRICITY {today.isoformat()} (GraphQL)", energy_today, local_tz)
    _print_summary(
        f"ELECTRICITY {tomorrow.isoformat()} (GraphQL)",
        energy_tomorrow,
        local_tz,
    )


if __name__ == "__main__":
    asyncio.run(main())
