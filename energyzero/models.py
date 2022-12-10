"""Data models for the EnergyZero API."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable


def _now() -> datetime:
    """Return the current time.

    Returns:
        The current time.
    """
    return datetime.now(timezone.utc)


def _get_pricetime(
    hourprices: dict[datetime, float], func: Callable[[dict[datetime, float]], datetime]
) -> datetime:
    """Return the time of the price.

    Args:
        hourprices: A dictionary with the hourprices.
        func: A function to get the time.

    Returns:
        The time of the price.
    """
    return func(hourprices, key=hourprices.get)  # type: ignore


@dataclass
class Electricity:
    """Object representing electricity data."""

    hourprices: dict[datetime, float]

    @property
    def current_hourprice(self) -> float | None:
        """Return the current hourprice.

        Returns:
            The current hourprice or None if the current hour is not in the hourprices.
        """
        for hour, price in self.hourprices.items():
            if hour <= _now() < hour + timedelta(hours=1):
                return price
        return None

    @property
    def next_hourprice(self) -> float | None:
        """Return the next hourprice.

        Returns:
            The next hourprice or None if the next hour is not in the hourprices.
        """
        for hour, price in self.hourprices.items():
            if hour - timedelta(hours=1) <= _now() < hour:
                return price
        return None

    @property
    def max_price(self) -> float:
        """Return the maximum price.

        Returns:
            The maximum price.
        """
        return max(self.hourprices.values())

    @property
    def min_price(self) -> float:
        """Return the minimum price.

        Returns:
            The minimum price.
        """
        return min(self.hourprices.values())

    @property
    def average_price(self) -> float:
        """Return the average price.

        Returns:
            The average price.
        """
        return round(sum(self.hourprices.values()) / len(self.hourprices.values()), 2)

    @property
    def highest_price_time(self) -> datetime:
        """Return the time of the maximum price.

        Returns:
            The time of the maximum price.
        """
        return _get_pricetime(self.hourprices, max)

    @property
    def lowest_price_time(self) -> datetime:
        """Return the time of the minimum price.

        Returns:
            The time of the minimum price.
        """
        return _get_pricetime(self.hourprices, min)

    @property
    def timestamp_prices(self) -> list[Any]:
        """Return a list of prices with timestamp.

        Returns:
            list of prices with timestamp
        """
        timestamp_prices: list[Any] = []
        for hour, price in self.hourprices.items():
            str_hour = str(hour)
            timestamp_prices.append({"time": str_hour, "value": price})
        return timestamp_prices

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Electricity:
        """Create an Electricity object from a dictionary.

        Args:
            data: A dictionary with the data from the API.

        Returns:
            An Electricity object.
        """

        hourprices: dict[datetime, float] = {}
        for item in data["Prices"]:
            hourprices[
                datetime.strptime(item["readingDate"], "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc
                )
            ] = item["price"]

        return cls(
            hourprices=hourprices,
        )


@dataclass
class Gas:
    """Object representing gas data."""

    hourprices: dict[datetime, float]

    @property
    def current_hourprice(self) -> float | None:
        """Return the current hourprice.

        Returns:
            The current hourprice or None if the current hour is not in the hourprices.
        """
        for hour, price in self.hourprices.items():
            if hour <= _now() < hour + timedelta(hours=1):
                return price
        return None

    @property
    def next_hourprice(self) -> float | None:
        """Return the next hourprice.

        Returns:
            The next hourprice or None if the next hour is not in the hourprices.
        """
        for hour, price in self.hourprices.items():
            if hour - timedelta(hours=1) <= _now() < hour:
                return price
        return None

    @property
    def max_price(self) -> float:
        """Return the maximum price.

        Returns:
            The maximum price.
        """
        return max(self.hourprices.values())

    @property
    def min_price(self) -> float:
        """Return the minimum price.

        Returns:
            The minimum price.
        """
        return min(self.hourprices.values())

    @property
    def average_price(self) -> float:
        """Return the average price.

        Returns:
            The average price.
        """
        return round(sum(self.hourprices.values()) / len(self.hourprices.values()), 2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Gas:
        """Create a Gas object from a dictionary.

        Args:
            data: A dictionary with the data from the API.

        Returns:
            A Gas object.
        """

        hourprices: dict[datetime, float] = {}
        for item in data["Prices"]:
            hourprices[
                datetime.strptime(item["readingDate"], "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc
                )
            ] = item["price"]

        return cls(
            hourprices=hourprices,
        )
