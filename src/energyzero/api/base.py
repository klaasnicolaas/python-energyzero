"""Base protocol for EnergyZero API clients."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Protocol, overload

from energyzero.const import PriceType

if TYPE_CHECKING:
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
        before any request. Invalid values raise TypeError before any request.
        All requested types use one backend request.

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
        before any request. Invalid values raise TypeError before any request.
        All requested types use one backend request.

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


def _normalize_price_types(
    price_type: PriceType | Iterable[PriceType],
) -> tuple[PriceType, ...]:
    """Validate requested price types and deduplicate in first-requested order."""
    if isinstance(price_type, PriceType):
        return (price_type,)

    if isinstance(price_type, (str, bytes)) or not isinstance(price_type, Iterable):
        msg = "price_type must be a PriceType or an iterable of PriceType values."
        raise TypeError(msg)

    requested_types = tuple(price_type)
    if not requested_types:
        msg = "At least one price type is required."
        raise ValueError(msg)

    if any(not isinstance(item, PriceType) for item in requested_types):
        msg = "Every item in price_type must be a PriceType value."
        raise TypeError(msg)

    return tuple(dict.fromkeys(requested_types))
