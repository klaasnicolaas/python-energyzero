"""Data models for the EnergyZero API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, tzinfo
from typing import Any

from .const import PriceType
from .exceptions import EnergyZeroNoDataError

REST_PRICE_STREAMS: dict[PriceType, str] = {
    PriceType.MARKET: "base",
    PriceType.MARKET_WITH_VAT: "base_with_vat",
    PriceType.ALL_IN_EXCL_VAT: "all_in",
    PriceType.ALL_IN: "all_in_with_vat",
}


def _value_at_time(moment: datetime, prices: dict[TimeRange, float]) -> float | None:
    """Return a function that returns a value at a specific time.

    Args:
    ----
        moment: The time to get the value for.
        prices: A dictionary with the prices.

    Returns:
    -------
        The value at the time.

    """
    value = None
    for timestamp_range, price in prices.items():
        if timestamp_range.contains(moment):
            value = price
            break
    return value


def _generate_timestamp_range_list(
    prices: dict[TimeRange, float],
) -> list[dict[str, float | TimeRange]]:
    """Return a list of timestamps.

    Args:
    ----
        prices: A dictionary with the hourprices.

    Returns:
    -------
        A list of timestamps.

    """
    return [
        {"timerange": timerange, "price": price} for timerange, price in prices.items()
    ]


def _parse_datetime_str(datetime_str: str) -> datetime:
    return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


@dataclass(frozen=True)
class TimeRange:
    """Object representing a range of time specified by a start and end time."""

    start_including: datetime
    end_excluding: datetime

    def contains(self, time: datetime) -> bool:
        """Check if this range contains the specified time.

        Args:
        ----
            time: The time to check against.

        """
        return self.start_including <= time < self.end_excluding

    def astimezone(self, tz: tzinfo | None = None) -> TimeRange:
        """Convert range to the specified time zone.

        Args:
        ----
            tz: The target time zone.

        Returns:
        -------
            The current range in the specified time zone.

        """
        return TimeRange(
            self.start_including.astimezone(tz), self.end_excluding.astimezone(tz)
        )

    def __str__(self) -> str:
        """Return a human readable string representation of this range."""
        format_string = "%Y-%m-%d %H:%M:%S"

        return (
            f"{self.start_including.strftime(format_string)} - "
            f"{self.end_excluding.strftime(format_string)}"
        )


@dataclass
class EnergyPriceBlock:
    """Object representing a block of energy prices."""

    time_range: TimeRange
    energy_price_excl: float
    energy_price_incl: float
    vat: float
    additional_costs: list[dict[str, float]]

    @property
    def total_excl(self) -> float:
        """Return the total price excluding VAT and additional costs."""
        return self.energy_price_excl + sum(
            cost["priceExcl"] for cost in self.additional_costs
        )

    @property
    def total_incl(self) -> float:
        """Return the total price including VAT and additional costs."""
        return self.energy_price_incl + sum(
            cost["priceIncl"] for cost in self.additional_costs
        )


@dataclass
class EnergyPrices:
    """Object representing energy price data.

    Can represent both electricity and gas price data. All time ranges are in UTC.

    """

    prices: dict[TimeRange, float]
    average_price: float | None
    raw_blocks: list[EnergyPriceBlock] = field(default_factory=list)

    @property
    def current_price(self) -> float | None:
        """Return the price at the current time.

        Returns
        -------
            The price for the current time.

        """
        return self.price_at_time(self.utcnow())

    @property
    def extreme_prices(self) -> tuple[float, float]:
        """Return the minimum and maximum price.

        Returns
        -------
            The minimum and maximum price.

        Raises
        ------
            EnergyZeroNoDataError: If no prices are available.

        """
        if len(self.prices) == 0:
            msg = "No prices available"
            raise EnergyZeroNoDataError(message=msg)

        return min(self.prices.values()), max(self.prices.values())

    @property
    def highest_price_time_range(self) -> TimeRange:
        """Return the UTC time range of the maximum price.

        Returns
        -------
            The UTC time range of the maximum price.

        Raises
        ------
            EnergyZeroNoDataError: If no prices are available.

        """
        if len(self.prices) == 0:
            msg = "No prices available"
            raise EnergyZeroNoDataError(message=msg)

        max_range, _ = max(self.prices.items(), key=lambda kv: kv[1])
        return max_range

    @property
    def lowest_price_time_range(self) -> TimeRange:
        """Return the UTC time range of the minimum price.

        Returns
        -------
            The UTC time range of the minimum price.

        Raises
        ------
            EnergyZeroNoDataError: If no prices are available.

        """
        if len(self.prices) == 0:
            msg = "No prices available"
            raise EnergyZeroNoDataError(message=msg)

        min_range, _ = min(self.prices.items(), key=lambda kv: kv[1])
        return min_range

    @property
    def pct_of_max_price(self) -> float:
        """Return the percentage of the maximum price.

        Returns
        -------
            The percentage of the maximum price.

        Raises
        ------
            EnergyZeroNoDataError: If no prices are available.

        """
        current: float = self.current_price or 0
        extreme_prices = self.extreme_prices

        return round((current / extreme_prices[1]) * 100, 2)

    @property
    def timestamp_prices(self) -> list[dict[str, float | TimeRange]]:
        """Return a list of prices with UTC time ranges.

        Returns
        -------
            list of prices with UTC time ranges.

        """
        return _generate_timestamp_range_list(self.prices)

    @property
    def time_ranges_priced_equal_or_lower(self) -> int:
        """Return the number of time ranges with prices <= current price.

        Returns
        -------
            The number of time ranges with prices equal or lower than the current price.

        Raises
        ------
            EnergyZeroNoDataError: If no prices are available.

        """
        if len(self.prices) == 0:
            msg = "No prices available"
            raise EnergyZeroNoDataError(message=msg)

        current: float = self.current_price or 0
        return sum(price <= current for price in self.prices.values())

    def utcnow(self) -> datetime:
        """Return the current timestamp in the UTC timezone.

        Returns
        -------
            The current timestamp in the UTC timezone.

        """
        return datetime.now(UTC)

    def price_at_time(self, moment: datetime) -> float | None:
        """Return the price at a specific UTC time.

        Args:
        ----
            moment: The UTC time to get the price for.

        Returns:
        -------
            The price at the specific UTC time.

        """
        value = _value_at_time(moment, self.prices)
        if value is not None or value == 0:
            return value
        return None

    @classmethod
    def from_dict(
        cls: type[EnergyPrices],
        data: dict[str, Any],
        price_type: PriceType = PriceType.ALL_IN,
    ) -> EnergyPrices:
        """Create an Energy object from a dictionary.

        Uses a dictionary as returned by the GraphQL endpoint.

        Args:
        ----
            data: A dictionary with the data from the API.
            price_type: Desired price flavor. Refer to ``PriceType`` for the available
                market/all-in options with or without VAT.

        Returns:
        -------
            An EnergyPrices object.

        """
        prices: dict[TimeRange, float] = {}
        blocks: list[EnergyPriceBlock] = []
        source_market_prices = data["energyMarketPrices"]["prices"]

        price_sum = 0

        for item in source_market_prices:
            key = TimeRange(
                _parse_datetime_str(item["from"]), _parse_datetime_str(item["till"])
            )
            additional_costs = item.get("additionalCosts", [])

            if price_type == PriceType.ALL_IN:
                price = item["energyPriceIncl"] + sum(
                    cost["priceIncl"] for cost in additional_costs
                )
            elif price_type == PriceType.ALL_IN_EXCL_VAT:
                price = item["energyPriceExcl"] + sum(
                    cost["priceExcl"] for cost in additional_costs
                )
            elif price_type == PriceType.MARKET_WITH_VAT:
                price = item["energyPriceIncl"]
            else:  # PriceType.MARKET
                price = item["energyPriceExcl"]

            prices[key] = price
            price_sum += price

            blocks.append(
                EnergyPriceBlock(
                    time_range=key,
                    energy_price_excl=item["energyPriceExcl"],
                    energy_price_incl=item["energyPriceIncl"],
                    vat=item.get("vat", 0),
                    additional_costs=item.get("additionalCosts", []),
                )
            )

        average_price = None
        if len(source_market_prices) > 0:
            average_price = price_sum / len(source_market_prices)

        return cls(
            prices=prices,
            average_price=average_price,
            raw_blocks=blocks,
        )

    @classmethod
    def from_rest_dict(
        cls: type[EnergyPrices],
        data: dict[str, Any],
        price_type: PriceType = PriceType.ALL_IN,
        filter_date: date | None = None,
    ) -> EnergyPrices:
        """Create an EnergyPrices object from a REST API response.

        Args:
        ----
            data: A dictionary with the data from the REST API.
            price_type: Desired price flavor. Refer to ``PriceType`` for the available
                market/all-in options with or without VAT.
            filter_date: Optional local date that should be retained. Entries
                outside of this local date are discarded.

        Returns:
        -------
            An EnergyPrices object.

        """
        prices: dict[TimeRange, float] = {}

        source_prices = data[REST_PRICE_STREAMS[price_type]]

        local_tz = None
        if filter_date:
            local_tz = datetime.now().astimezone().tzinfo or UTC

        for item in source_prices:
            start_time = _parse_datetime_str(item["start"])
            end_time = _parse_datetime_str(item["end"])
            price = float(item["price"]["value"])

            key = TimeRange(start_time, end_time)
            if filter_date and local_tz:
                start_local_date = key.start_including.astimezone(local_tz).date()
                if start_local_date != filter_date:
                    continue

            prices[key] = price

        average_price = None
        if prices:
            average_price = sum(prices.values()) / len(prices)

        return cls(
            prices=prices,
            average_price=average_price,
            raw_blocks=[],  # REST API doesn't provide detailed blocks
        )
