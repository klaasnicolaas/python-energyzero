"""Data models for the EnergyZero API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


def _timed_value(moment: datetime, prices: dict[datetime, float]) -> float | None:
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
    for timestamp, price in prices.items():
        future_ts = timestamp + timedelta(hours=1)
        if timestamp <= moment < future_ts:
            value = price
    return value


def _get_pricetime(
    prices: dict[datetime, float],
    func: Callable[[dict[datetime, float]], datetime],
) -> datetime:
    """Return the time of the price.

    Args:
    ----
        prices: A dictionary with the hourprices.
        func: A function to get the time.

    Returns:
    -------
        The time of the price.

    """
    return func(prices, key=prices.get)  # type: ignore[call-arg]


def _generate_timestamp_list(
    prices: dict[datetime, float],
) -> list[dict[str, float | datetime]]:
    """Return a list of timestamps.

    Args:
    ----
        prices: A dictionary with the hourprices.

    Returns:
    -------
        A list of timestamps.

    """
    return [
        {"timestamp": timestamp, "price": price} for timestamp, price in prices.items()
    ]


@dataclass
class Electricity:
    """Object representing electricity data."""

    prices: dict[datetime, float]
    average_price: float

    @property
    def current_price(self) -> float | None:
        """Return the current hourprice.

        Returns
        -------
            The price for the current hour.

        """
        return self.price_at_time(self.utcnow())

    @property
    def extreme_prices(self) -> tuple[float, float]:
        """Return the minimum and maximum price.

        Returns
        -------
            The minimum and maximum price.

        """
        return min(self.prices.values()), max(self.prices.values())

    @property
    def highest_price_time(self) -> datetime:
        """Return the time of the maximum price.

        Returns
        -------
            The time of the maximum price.

        """
        return _get_pricetime(self.prices, max)

    @property
    def lowest_price_time(self) -> datetime:
        """Return the time of the minimum price.

        Returns
        -------
            The time of the minimum price.

        """
        return _get_pricetime(self.prices, min)

    @property
    def pct_of_max_price(self) -> float:
        """Return the percentage of the maximum price.

        Returns
        -------
            The percentage of the maximum price.

        """
        current: float = self.current_price or 0
        return round((current / self.extreme_prices[1]) * 100, 2)

    @property
    def timestamp_prices(self) -> list[dict[str, float | datetime]]:
        """Return a list of prices with timestamp.

        Returns
        -------
            list of prices with timestamp

        """
        return _generate_timestamp_list(self.prices)

    @property
    def hours_priced_equal_or_lower(self) -> int:
        """Return the number of hours with prices equal or lower than the current price.

        Returns
        -------
            The number of hours with prices equal or lower than the current price.

        """
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
        """Return the price at a specific time.

        Args:
        ----
            moment: The time to get the price for.

        Returns:
        -------
            The price at the specific time.

        """
        value = _timed_value(moment, self.prices)
        if value is not None or value == 0:
            return value
        return None

    @classmethod
    def from_dict(cls: type[Electricity], data: dict[str, Any]) -> Electricity:
        """Create an Electricity object from a dictionary.

        Args:
        ----
            data: A dictionary with the data from the API.

        Returns:
        -------
            An Electricity object.

        """
        prices: dict[datetime, float] = {}
        for item in data["Prices"]:
            prices[
                datetime.strptime(item["readingDate"], "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=UTC,
                )
            ] = item["price"]

        return cls(
            prices=prices,
            average_price=data["average"],
        )


@dataclass
class Gas:
    """Object representing gas data."""

    prices: dict[datetime, float]
    average_price: float

    @property
    def current_price(self) -> float | None:
        """Return the current gas price.

        Returns
        -------
            The price for the current hour.

        """
        return self.price_at_time(self.utcnow())

    @property
    def extreme_prices(self) -> tuple[float, float]:
        """Return the minimum and maximum price.

        Returns
        -------
            The minimum and maximum price.

        """
        return min(self.prices.values()), max(self.prices.values())

    @property
    def timestamp_prices(self) -> list[dict[str, float | datetime]]:
        """Return a list of prices with timestamp.

        Returns
        -------
            list of prices with timestamp

        """
        return _generate_timestamp_list(self.prices)

    def utcnow(self) -> datetime:
        """Return the current timestamp in the UTC timezone.

        Returns
        -------
            The current timestamp in the UTC timezone.

        """
        return datetime.now(UTC)

    def price_at_time(self, moment: datetime) -> float | None:
        """Return the price at a specific time.

        Args:
        ----
            moment: The time to get the price for.

        Returns:
        -------
            The price at the specific time.

        """
        value = _timed_value(moment, self.prices)
        if value is not None or value == 0:
            return value
        return None

    @classmethod
    def from_dict(cls: type[Gas], data: dict[str, Any]) -> Gas:
        """Create a Gas object from a dictionary.

        Args:
        ----
            data: A dictionary with the data from the API.

        Returns:
        -------
            A Gas object.

        """
        prices: dict[datetime, float] = {}
        for item in data["Prices"]:
            prices[
                datetime.strptime(item["readingDate"], "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=UTC,
                )
            ] = item["price"]

        return cls(
            prices=prices,
            average_price=data["average"],
        )
