"""Asynchronous example: hourly electricity prices via REST API."""

import asyncio
from datetime import UTC, date, datetime, timedelta

from energyzero import (  # pyright: ignore[reportMissingImports]
    EnergyPrices,
    EnergyZero,
    EnergyZeroConnectionError,
    EnergyZeroNoDataError,
    Interval,
    PriceType,
)


def _price_to_string(price: float | None) -> str:
    if price is None:
        return "Unknown"
    return f"EUR {price:0.3f}/kWh"


async def _fetch_day(client: EnergyZero, target_date: date) -> EnergyPrices | None:
    try:
        return await client.get_electricity_prices(
            start_date=target_date,
            interval=Interval.HOUR,
            price_type=PriceType.ALL_IN,
        )
    except (EnergyZeroConnectionError, EnergyZeroNoDataError) as err:
        print(f"No data available for {target_date.isoformat()}: {err}")
        return None


def _print_summary(label: str, data: EnergyPrices) -> None:
    print(f"--- {label} ---")
    if len(data.prices) == 0:
        print("No electricity data available")
        return

    min_price, max_price = data.extreme_prices
    print(f"Average price: {_price_to_string(data.average_price)}")
    print(f"Min price: {_price_to_string(min_price)}")
    print(f"Max price: {_price_to_string(max_price)}")
    print(f"Lowest time: {data.lowest_price_time_range.astimezone()}")
    print(f"Highest time: {data.highest_price_time_range.astimezone()}")

    current = data.current_price
    if current is not None:
        print(f"Current price: {_price_to_string(current)}")
        print(f"Percent of max: {data.pct_of_max_price}%")

    next_hour = data.price_at_time(data.utcnow() + timedelta(hours=1))
    if next_hour is not None:
        print(f"Next hour price: {_price_to_string(next_hour)}")

    print(f"Blocks <= current price: {data.time_ranges_priced_equal_or_lower}")
    print()


async def main() -> None:
    """Fetch hourly electricity prices for today and tomorrow via REST."""
    async with EnergyZero() as client:
        today = datetime.now(UTC).astimezone().date()
        tomorrow = today + timedelta(days=1)
        prices_today = await _fetch_day(client, today)
        prices_tomorrow = await _fetch_day(client, tomorrow)

    if prices_today:
        _print_summary(f"ELECTRICITY {today.isoformat()} (REST, hourly)", prices_today)
    if prices_tomorrow:
        _print_summary(
            f"ELECTRICITY {tomorrow.isoformat()} (REST, hourly)",
            prices_tomorrow,
        )


if __name__ == "__main__":
    asyncio.run(main())
