"""Asynchronous example: gas prices via REST API."""

import asyncio
from datetime import UTC, datetime

from energyzero import (  # pyright: ignore[reportMissingImports]
    EnergyPrices,
    EnergyZero,
    PriceType,
)


def _price_to_string(price: float | None) -> str:
    if price is None:
        return "Unknown"
    return f"€{price:0.3f}"


def _print_summary(data: EnergyPrices) -> None:
    if len(data.prices) == 0:
        print("No gas data available")
        return

    min_price, max_price = data.extreme_prices
    print(f"Average price: {_price_to_string(data.average_price)}")
    print(f"Min price: {_price_to_string(min_price)}")
    print(f"Max price: {_price_to_string(max_price)}")

    current = data.current_price
    if current is not None:
        print(f"Current price: {_price_to_string(current)}")
        print(f"Percent of max: {data.pct_of_max_price}%")

    print(f"Days <= current price: {data.time_ranges_priced_equal_or_lower}")


async def main() -> None:
    """Fetch current gas price via REST API."""
    async with EnergyZero() as client:
        today = datetime.now(UTC).astimezone().date()
        prices = await client.get_gas_prices(
            start_date=today,
            price_type=PriceType.ALL_IN,
        )

    print(f"--- GAS {today.isoformat()} (REST) ---")
    _print_summary(prices)


if __name__ == "__main__":
    asyncio.run(main())
