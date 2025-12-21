"""GraphQL API client for EnergyZero."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from importlib import metadata
from typing import Any

from aiohttp.client import ClientError, ClientSession
from aiohttp.hdrs import METH_POST
from yarl import URL

from energyzero.const import PriceType
from energyzero.exceptions import (
    EnergyZeroConnectionError,
    EnergyZeroError,
    EnergyZeroNoDataError,
)
from energyzero.models import EnergyPrices

VERSION = metadata.version("energyzero")


@dataclass
class GraphQLClient:
    """GraphQL API client for EnergyZero."""

    request_timeout: float = 10.0
    session: ClientSession | None = None

    _close_session: bool = False

    def to_datetime_string(
        self, base_date: date, delta: timedelta = timedelta(0)
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
        local_tz = datetime.now(UTC).astimezone().tzinfo
        date_utc = (
            datetime(
                base_date.year,
                base_date.month,
                base_date.day,
                tzinfo=local_tz,
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

    async def get_electricity_prices(
        self,
        start_date: date,
        end_date: date | None = None,
        interval: str = "INTERVAL_QUARTER",
        price_type: PriceType = PriceType.ALL_IN,
    ) -> EnergyPrices:
        """Get electricity prices using GraphQL API.

        Args:
        ----
            start_date: Start date (local timezone).
            end_date: Optional end date (GraphQL requires this value).
            interval: Interval type (ignored, GraphQL only supports hourly).
            price_type: Desired price flavor. See ``PriceType`` for options.

        Returns:
        -------
            An EnergyPrices object.

        Raises:
        ------
            EnergyZeroNoDataError: No data found.

        """
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

        return EnergyPrices.from_dict(data["data"], price_type)

    async def get_gas_prices(
        self,
        start_date: date,
        end_date: date | None = None,
        price_type: PriceType = PriceType.ALL_IN,
    ) -> EnergyPrices:
        """Get gas prices using GraphQL API.

        Args:
        ----
            start_date: Start date (local timezone).
            end_date: Optional end date (GraphQL requires this value).
            price_type: ALL_IN or MARKET prices.

        Returns:
        -------
            An EnergyPrices object.

        Raises:
        ------
            EnergyZeroNoDataError: No data found.

        """
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

        return EnergyPrices.from_dict(data["data"], price_type)

    async def close(self) -> None:
        """Close the client session."""
        if self.session and self._close_session:
            await self.session.close()
