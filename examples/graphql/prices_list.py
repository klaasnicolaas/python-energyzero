"""Asynchronous example: List of electricity and gas prices via GraphQL."""

import asyncio
from datetime import datetime, tzinfo

import pytz

from energyzero import EnergyZero, TimeRange, VatOption


def _price_to_string(price: float | None) -> str:
    if price is None:
        return "Unknown"
    return f"€{price:0.2f} (€{price})"


def _range_and_price_to_str(time_range: TimeRange, price: float, tz: tzinfo) -> str:
    return f"{time_range.astimezone(tz)}: {_price_to_string(price)}"


def _price_list_item_to_str(entry: dict[str, float | TimeRange], tz: tzinfo) -> str:
    time_range = entry["timerange"]
    price = entry["price"]

    if (not isinstance(time_range, TimeRange)) or (not isinstance(price, float)):
        msg = "Dictionary does not contain a valid timerange-price combination"
        raise TypeError(msg)

    return _range_and_price_to_str(time_range, price, tz)


async def main() -> None:
    """Show example on fetching the electricity and gas prices from EnergyZero."""
    async with EnergyZero(vat=VatOption.INCLUDE) as client:
        local_tz = pytz.timezone("Europe/Amsterdam")
        today = datetime.now(local_tz).date()

        energy = await client.get_electricity_prices(start_date=today, end_date=today)
        gas = await client.get_gas_prices(start_date=today, end_date=today)

        electricity_prices_str = (
            _price_list_item_to_str(entry, local_tz)
            for entry in energy.timestamp_prices
        )
        gas_prices_str = (
            _price_list_item_to_str(entry, local_tz) for entry in gas.timestamp_prices
        )

        print("--- ELECTRICITY ---")
        print("\n".join(electricity_prices_str))
        print("\n--- GAS ---")
        print("\n".join(gas_prices_str))


if __name__ == "__main__":
    asyncio.run(main())
