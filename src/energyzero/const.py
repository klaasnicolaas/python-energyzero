"""Constants for EnergyZero API client."""

from __future__ import annotations

from enum import Enum, IntEnum


class VatOption(str, Enum):
    """Enum representing whether to include VAT or not."""

    INCLUDE = "true"
    EXCLUDE = "false"


class PriceType(Enum):
    """Enum representing what kind of prices to return."""

    MARKET = 1
    ALL_IN = 2


class Interval(IntEnum):
    """Enum representing the time intervals of prices."""

    DAY = 4
    MONTH = 5
    YEAR = 6
    WEEK = 9
