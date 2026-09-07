"""Base protocol for EnergyZero API clients."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, overload

from energyzero.const import PriceType

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import date, tzinfo

    from energyzero.models import EnergyPrices


class EnergyZeroAPIProtocol(Protocol):
    """Protocol defining the interface for EnergyZero API clients."""

    @overload
    async def get_electricity_prices(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None = None,
        interval: str = "INTERVAL_QUARTER",
        price_type: PriceType = PriceType.ALL_IN,
        *,
        local_tz: tzinfo | None = None,
    ) -> EnergyPrices: ...

    @overload
    async def get_electricity_prices(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None,
        interval: str,
        price_type: Iterable[PriceType],
        *,
        local_tz: tzinfo | None = None,
    ) -> dict[PriceType, EnergyPrices]: ...

    @overload
    async def get_electricity_prices(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None = None,
        interval: str = "INTERVAL_QUARTER",
        *,
        price_type: Iterable[PriceType],
        local_tz: tzinfo | None = None,
    ) -> dict[PriceType, EnergyPrices]: ...

    async def get_electricity_prices(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None = None,
        interval: str = "INTERVAL_QUARTER",
        price_type: PriceType | Iterable[PriceType] = PriceType.ALL_IN,
        *,
        local_tz: tzinfo | None = None,
    ) -> EnergyPrices | dict[PriceType, EnergyPrices]:
        """Get electricity prices for a given period.

        Iterable input always returns a mapping, even for one type. Duplicates
        appear once, in first-requested order. Empty iterables raise ValueError
        before any request. All requested types use one backend request.

        Args:
        ----
            start_date: Start date of the period (local timezone).
            end_date: Optional end date (GraphQL requires this parameter; REST
                requires an identical date and only supports single-day requests).
            interval: Interval type (INTERVAL_QUARTER, INTERVAL_HOUR).
            price_type: One PriceType or an iterable of types (default: ALL_IN).
            local_tz: Timezone used to interpret the requested local date range.

        Returns:
        -------
            One EnergyPrices for a single PriceType; a mapping for an iterable.

        """
        raise NotImplementedError

    @overload
    async def get_gas_prices(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None = None,
        price_type: PriceType = PriceType.ALL_IN,
        *,
        local_tz: tzinfo | None = None,
    ) -> EnergyPrices: ...

    @overload
    async def get_gas_prices(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None,
        price_type: Iterable[PriceType],
        *,
        local_tz: tzinfo | None = None,
    ) -> dict[PriceType, EnergyPrices]: ...

    @overload
    async def get_gas_prices(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None = None,
        *,
        price_type: Iterable[PriceType],
        local_tz: tzinfo | None = None,
    ) -> dict[PriceType, EnergyPrices]: ...

    async def get_gas_prices(  # pylint: disable=too-many-arguments
        self,
        start_date: date,
        end_date: date | None = None,
        price_type: PriceType | Iterable[PriceType] = PriceType.ALL_IN,
        *,
        local_tz: tzinfo | None = None,
    ) -> EnergyPrices | dict[PriceType, EnergyPrices]:
        """Get gas prices for a given period.

        Iterable input always returns a mapping, even for one type. Duplicates
        appear once, in first-requested order. Empty iterables raise ValueError
        before any request. All requested types use one backend request.

        Args:
        ----
            start_date: Start date of the period (local timezone).
            end_date: Optional end date (GraphQL requires this parameter; REST
                requires an identical date and only supports single-day requests).
            price_type: One PriceType or an iterable of types (default: ALL_IN).
            local_tz: Timezone used to interpret the requested local date range.

        Returns:
        -------
            One EnergyPrices for a single PriceType; a mapping for an iterable.

        """
        raise NotImplementedError

    async def close(self) -> None:
        """Close the API client and cleanup resources."""
        raise NotImplementedError
