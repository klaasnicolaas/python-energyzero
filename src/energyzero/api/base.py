"""Base protocol for EnergyZero API clients."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from energyzero.const import PriceType

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import date, tzinfo

    from energyzero.models import EnergyPrices


class EnergyZeroAPIProtocol(Protocol):
    """Protocol defining the interface for EnergyZero API clients."""

    async def get_electricity_prices(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None = None,
        interval: str = "INTERVAL_QUARTER",
        price_type: PriceType = PriceType.ALL_IN,
        *,
        local_tz: tzinfo | None = None,
    ) -> EnergyPrices:
        """Get electricity prices for a given period.

        Args:
        ----
            start_date: Start date of the period (local timezone).
            end_date: Optional end date (GraphQL requires this parameter; REST
                requires an identical date and only supports single-day requests).
            interval: Interval type (INTERVAL_QUARTER, INTERVAL_HOUR).
            price_type: Type of price (ALL_IN or MARKET).
            local_tz: Timezone used to interpret the requested local date range.

        Returns:
        -------
            An EnergyPrices object.

        """
        raise NotImplementedError

    async def get_electricity_prices_by_type(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None = None,
        interval: str = "INTERVAL_QUARTER",
        *,
        price_types: Iterable[PriceType],
        local_tz: tzinfo | None = None,
    ) -> dict[PriceType, EnergyPrices]:
        """Get multiple electricity price types with one backend request.

        Uses the same date, timezone and interval semantics as
        ``get_electricity_prices``. Values are in EUR/kWh.
        ``price_types`` accepts an iterable; duplicates are returned once,
        in first-requested order. An empty iterable raises ``ValueError``
        before making a request. Returns a mapping of types to EnergyPrices.
        """
        raise NotImplementedError

    async def get_gas_prices(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None = None,
        price_type: PriceType = PriceType.ALL_IN,
        *,
        local_tz: tzinfo | None = None,
    ) -> EnergyPrices:
        """Get gas prices for a given period.

        Args:
        ----
            start_date: Start date of the period (local timezone).
            end_date: Optional end date (GraphQL requires this parameter; REST
                requires an identical date and only supports single-day requests).
            price_type: Type of price (ALL_IN or MARKET).
            local_tz: Timezone used to interpret the requested local date range.

        Returns:
        -------
            An EnergyPrices object.

        """
        raise NotImplementedError

    async def get_gas_prices_by_type(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None = None,
        *,
        price_types: Iterable[PriceType],
        local_tz: tzinfo | None = None,
    ) -> dict[PriceType, EnergyPrices]:
        """Get multiple gas price types with one backend request.

        Uses the same date, timezone and interval semantics as
        ``get_gas_prices``. Values are in EUR/m³.
        ``price_types`` accepts an iterable; duplicates are returned once,
        in first-requested order. An empty iterable raises ``ValueError``
        before making a request. Returns a mapping of types to EnergyPrices.
        """
        raise NotImplementedError

    async def close(self) -> None:
        """Close the API client and cleanup resources."""
        raise NotImplementedError
