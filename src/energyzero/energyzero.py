"""Asynchronous Python client for the EnergyZero API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

from energyzero.api import APIBackend, EnergyZeroAPIProtocol
from energyzero.api.graphql import GraphQLClient
from energyzero.api.rest import RESTClient
from energyzero.const import Interval, PriceType

if TYPE_CHECKING:
    from datetime import date

    from aiohttp.client import ClientSession

    from energyzero.models import EnergyPrices


@dataclass
class EnergyZero:
    """Main EnergyZero client - delegates to backend-specific API clients."""

    backend: APIBackend = APIBackend.REST
    request_timeout: float = 10.0
    session: ClientSession | None = None

    _client: EnergyZeroAPIProtocol = field(init=False, repr=False)
    _close_session: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the appropriate backend client."""
        if self.backend == APIBackend.REST:
            self._client = RESTClient(
                request_timeout=self.request_timeout,
                session=self.session,
            )
        elif self.backend == APIBackend.GRAPHQL:
            self._client = GraphQLClient(
                request_timeout=self.request_timeout,
                session=self.session,
            )
        else:
            msg = f"Unknown backend: {self.backend}"
            raise ValueError(msg)

        if self.session is None:
            self._close_session = True

    async def get_electricity_prices(
        self,
        start_date: date,
        end_date: date | None = None,
        interval: Interval | str = Interval.QUARTER,
        price_type: PriceType = PriceType.ALL_IN,
    ) -> EnergyPrices:
        """Get electricity prices for a given period.

        Args:
        ----
            start_date: Start date of the period (local timezone).
            end_date: Optional end date (mandatory for GraphQL; REST uses a
                single-day request and ignores this value).
            interval: Interval type:
                - "INTERVAL_QUARTER": Quarter-hour prices (15 min) - default
                - "INTERVAL_HOUR": Hourly prices
            price_type: Desired price flavor. See ``PriceType`` for the available
                market/all-in options with or without VAT (default: ``ALL_IN``).

        Returns:
        -------
            An EnergyPrices object with the requested prices.

        """
        interval_value = interval.value if isinstance(interval, Interval) else interval
        return await self._client.get_electricity_prices(
            start_date, end_date, interval_value, price_type
        )

    async def get_gas_prices(
        self,
        start_date: date,
        end_date: date | None = None,
        price_type: PriceType = PriceType.ALL_IN,
    ) -> EnergyPrices:
        """Get gas prices for a given period.

        Args:
        ----
            start_date: Start date of the period (local timezone).
            end_date: Optional end date (mandatory for GraphQL; REST uses a
                single-day request and ignores this value).
            price_type: Desired price flavor. See ``PriceType`` for the available
                market/all-in options with or without VAT (default: ``ALL_IN``).

        Returns:
        -------
            An EnergyPrices object with the requested prices.

        """
        return await self._client.get_gas_prices(start_date, end_date, price_type)

    async def close(self) -> None:
        """Close open client session."""
        await self._client.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The EnergyZero object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()
