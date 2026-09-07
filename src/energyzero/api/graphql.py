"""GraphQL API client for EnergyZero."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, tzinfo
from importlib import metadata
from typing import TYPE_CHECKING, Any, overload

from aiohttp.client import ClientError, ClientSession
from aiohttp.hdrs import METH_POST
from yarl import URL

from energyzero.api.base import _normalize_price_types
from energyzero.const import PriceType
from energyzero.exceptions import (
    EnergyZeroConnectionError,
    EnergyZeroError,
    EnergyZeroNoDataError,
)
from energyzero.models import EnergyPrices

if TYPE_CHECKING:
    from collections.abc import Iterable

VERSION = metadata.version("energyzero")


@dataclass
class GraphQLClient:
    """GraphQL API client for EnergyZero."""

    request_timeout: float = 10.0
    session: ClientSession | None = None

    _close_session: bool = False

    def to_datetime_string(
        self,
        base_date: date,
        delta: timedelta = timedelta(0),
    ) -> str:
        """Convert a local timezone date to a UTC datetime string.

        Args:
        ----
            base_date: The base date (local timezone) to convert.
            delta: A timedelta to add to the base date.

        Returns:
        -------
            A string representing the date in ISO 8601 format with UTC timezone.

        """
        timezone_to_use = datetime.now(UTC).astimezone().tzinfo
        date_utc = (
            datetime(
                base_date.year,
                base_date.month,
                base_date.day,
                tzinfo=timezone_to_use,
            ).astimezone(UTC)
            + delta
        )

        return date_utc.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    async def _request(
        self,
        uri: str,
        *,
        json: Any = None,
    ) -> Any:
        """Handle a request to the GraphQL API.

        Args:
        ----
            uri: Request URI path.
            json: JSON body for POST request.

        Returns:
        -------
            A Python dictionary with the response.

        Raises:
        ------
            EnergyZeroConnectionError: Connection error.
            EnergyZeroError: Unexpected response.

        """
        url = URL.build(scheme="https", host="api.energyzero.nl", path="/v1/").join(
            URL(uri),
        )

        headers = {
            "Accept": "application/json, text/plain",
            "User-Agent": f"PythonEnergyZero/{VERSION}",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(  # pyright: ignore[reportOptionalMemberAccess]
                    METH_POST,
                    url,
                    headers=headers,
                    ssl=True,
                    json=json,
                )
                response.raise_for_status()
        except TimeoutError as exception:
            msg = "Timeout occurred while connecting to the API."
            raise EnergyZeroConnectionError(message=msg) from exception
        except (ClientError, socket.gaierror) as exception:
            msg = "Error occurred while communicating with the API."
            raise EnergyZeroConnectionError(message=msg) from exception

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected content type response from the GraphQL API"
            raise EnergyZeroError(msg, {"Content-Type": content_type, "response": text})

        data = await response.json()
        errors_key = "errors"

        if errors_key in data:
            error_messages = ", ".join([item["message"] for item in data[errors_key]])
            msg = f"The API returned error(s): {error_messages}"
            raise EnergyZeroError(msg)

        return data

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
        """Get electricity prices using GraphQL API.

        Iterable input always returns a mapping, even for one type. Duplicates
        appear once, in first-requested order. Empty iterables raise ValueError
        before any request. Invalid values raise TypeError before any request.
        All requested types use one backend request.

        Args:
        ----
            start_date: Start date (local timezone).
            end_date: Optional end date (GraphQL requires this value).
            interval: Interval type (ignored, GraphQL only supports hourly).
            price_type: One PriceType or an iterable of types (default: ALL_IN).
            local_tz: Unused for GraphQL. Present for API compatibility.

        Returns:
        -------
            One EnergyPrices for a single PriceType; a mapping for an iterable.

        Raises:
        ------
            EnergyZeroNoDataError: No data found.

        """
        requested_types = _normalize_price_types(price_type)

        _ = interval  # GraphQL backend always returns hourly intervals.
        if end_date is None:
            msg = "end_date is required when using the GraphQL backend."
            raise ValueError(msg)

        gql_query = """
            query EnergyMarketPrices($input: EnergyMarketPricesInput!) {
            energyMarketPrices(input: $input) {
                averageExcl
                averageIncl
                prices {
                energyPriceExcl
                energyPriceIncl
                from
                isAverage
                till
                type
                vat
                additionalCosts {
                    name
                    priceExcl
                    priceIncl
                }
                }
            }
            }
            """

        _ = local_tz
        from_str = self.to_datetime_string(start_date)
        till_str = self.to_datetime_string(end_date, timedelta(days=1))

        data = await self._request(
            "gql",
            json={
                "query": gql_query,
                "variables": {
                    "input": {
                        "from": from_str,
                        "till": till_str,
                        "intervalType": "Hourly",
                        "type": "Electricity",
                    },
                },
                "operationName": "EnergyMarketPrices",
            },
        )

        if data["data"] == []:
            msg = "No energy prices found for this period."
            raise EnergyZeroNoDataError(message=msg)

        results = {
            requested_type: EnergyPrices.from_dict(data["data"], requested_type)
            for requested_type in requested_types
        }
        return results[price_type] if isinstance(price_type, PriceType) else results

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
        """Get gas prices using GraphQL API.

        Iterable input always returns a mapping, even for one type. Duplicates
        appear once, in first-requested order. Empty iterables raise ValueError
        before any request. Invalid values raise TypeError before any request.
        All requested types use one backend request.

        Args:
        ----
            start_date: Start date (local timezone).
            end_date: Optional end date (GraphQL requires this value).
            price_type: One PriceType or an iterable of types (default: ALL_IN).
            local_tz: Unused for GraphQL. Present for API compatibility.

        Returns:
        -------
            One EnergyPrices for a single PriceType; a mapping for an iterable.

        Raises:
        ------
            EnergyZeroNoDataError: No data found.

        """
        requested_types = _normalize_price_types(price_type)

        if end_date is None:
            msg = "end_date is required when using the GraphQL backend."
            raise ValueError(msg)

        gql_query = """
            query EnergyMarketPricesGas($input: EnergyMarketPricesInput!) {
            energyMarketPrices(input: $input) {
                averageExcl
                averageIncl
                prices {
                energyPriceExcl
                energyPriceIncl
                from
                isAverage
                till
                type
                vat
                additionalCosts {
                    name
                    priceExcl
                    priceIncl
                }
                }
            }
            }
            """

        # Gas prices are valid from 06:00 to 06:00 the next day
        _ = local_tz
        from_str = self.to_datetime_string(start_date, timedelta(hours=6, days=-1))
        till_str = self.to_datetime_string(end_date, timedelta(hours=6, days=1))

        data = await self._request(
            "gql",
            json={
                "query": gql_query,
                "variables": {
                    "input": {
                        "from": from_str,
                        "till": till_str,
                        "intervalType": "Daily",
                        "type": "Gas",
                    },
                },
                "operationName": "EnergyMarketPricesGas",
            },
        )

        if data["data"] == []:
            msg = "No gas prices found for this period."
            raise EnergyZeroNoDataError(message=msg)

        results = {
            requested_type: EnergyPrices.from_dict(data["data"], requested_type)
            for requested_type in requested_types
        }
        return results[price_type] if isinstance(price_type, PriceType) else results

    async def close(self) -> None:
        """Close the client session."""
        if self.session and self._close_session:
            await self.session.close()
