"""Constants for EnergyZero API client."""

from __future__ import annotations

from enum import Enum


class PriceType(str, Enum):
    """Enum describing the price flavor returned by the APIs."""

    MARKET = "market"
    ALL_IN = "all_in"
    MARKET_WITH_VAT = "market_with_vat"
    ALL_IN_EXCL_VAT = "all_in_excl_vat"


class Interval(str, Enum):
    """Interval constants for REST API."""

    QUARTER = "INTERVAL_QUARTER"
    HOUR = "INTERVAL_HOUR"
    DAY = "INTERVAL_DAY"
