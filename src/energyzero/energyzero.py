"""Asynchronous Python client for the EnergyZero API."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from importlib import metadata
from typing import Any, Self

from aiohttp.client import ClientError, ClientSession
from aiohttp.hdrs import METH_GET, METH_POST
from yarl import URL

from .const import Interval, PriceType, VatOption
from .exceptions import (
    EnergyZeroConnectionError,
    EnergyZeroError,
    EnergyZeroNoDataError,
)
from .models import Electricity, EnergyPrices, Gas

VERSION = metadata.version(__package__)


@dataclass
class EnergyZero:
    """Main class for handling data fetching from EnergyZero."""

    request_timeout: float = 10.0
    session: ClientSession | None = None

    _close_session: bool = False

    async def _request(
        self,
        uri: str,
        *,
        method: str = METH_GET,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        """Handle a request to the API of EnergyZero.

        Args:
        ----
            uri: Request URI, without '/', for example, 'status'
            method: HTTP method to use, for example, 'GET'
            params: Extra options to improve or limit the response.

        Returns:
        -------
            A Python dictionary (json) with the response from EnergyZero.

        Raises:
        ------
            EnergyZeroConnectionError: An error occurred while
                communicating with the API.
            EnergyZeroError: Received an unexpected response from
                the API.

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
                response = await self.session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    ssl=True,
                    json=json,
                )
                response.raise_for_status()
        except TimeoutError as exception:
            msg = "Timeout occurred while connecting to the API."
            raise EnergyZeroConnectionError(
                msg,
            ) from exception
        except (ClientError, socket.gaierror) as exception:
            msg = "Error occurred while communicating with the API."
            raise EnergyZeroConnectionError(
                msg,
            ) from exception

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected content type response from the EnergyZero API"
            raise EnergyZeroError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        data = await response.json()
        errors_key = "errors"

        if errors_key in data:
            error_messages = ", ".join([item["message"] for item in data[errors_key]])
            msg = f"The API returned error(s): {error_messages}"
            raise EnergyZeroError(
                msg,
            )

        return data

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

    async def get_gas_prices_legacy(
        self,
        start_date: date,
        end_date: date,
        interval: int = 4,
        vat: VatOption | None = None,
    ) -> Gas:
        """[LEGACY] Get gas prices for a given period.

        Args:
        ----
            start_date: Start date (local timezone) of the period.
            end_date: End date (local timezone) of the period.
            interval: Interval of the prices.
            vat: VAT category (included by default).

        Returns:
        -------
            A Python dictionary with the response from EnergyZero.

        Raises:
        ------
            EnergyZeroNoDataError: No gas prices found for this period.

        """
        local_tz = datetime.now(UTC).astimezone().tzinfo
        now: datetime = datetime.now(tz=local_tz)

        if now.hour >= 6 and now.hour <= 23:
            # Set start_date to 06:00:00 and the end_date to 05:59:59 next day
            # Convert to UTC time 04:00:00 and 03:59:59 next day
            utc_start_date_str = self.to_datetime_string(start_date, timedelta(hours=6))
            utc_end_date_str = self.to_datetime_string(
                end_date,
                timedelta(hours=5, minutes=59, seconds=59, milliseconds=999, days=1),
            )
        else:
            # Set start_date to 06:00:00 prev day and the end_date to 05:59:59
            # Convert to UTC time 04:00:00 prev day and 03:59:59 current day
            utc_start_date_str = self.to_datetime_string(
                start_date, timedelta(hours=6, days=-1)
            )
            utc_end_date_str = self.to_datetime_string(
                end_date, timedelta(hours=5, minutes=59, seconds=59, milliseconds=999)
            )
        data = await self._request(
            "energyprices",
            params={
                "fromDate": utc_start_date_str,
                "tillDate": utc_end_date_str,
                "interval": interval,
                "usageType": 3,
                "inclBtw": vat.value if vat is not None else VatOption.INCLUDE.value,
            },
        )

        if data["Prices"] == []:
            msg = "No gas prices found for this period."
            raise EnergyZeroNoDataError(msg)
        return Gas.from_dict(data)

    async def get_electricity_prices_legacy(
        self,
        start_date: date,
        end_date: date,
        interval: Interval = Interval.DAY,
        vat: VatOption | None = None,
    ) -> Electricity:
        """[LEGACY] Get energy prices for a given period.

        Args:
        ----
            start_date: Start date (local timezone) of the period.
            end_date: End date (local timezone) of the period.
            interval: Interval of the prices.
            vat: VAT category (included by default).

        Returns:
        -------
            A Python dictionary with the response from EnergyZero.

        Raises:
        ------
            EnergyZeroNoDataError: No energy prices found for this period.

        """
        data = await self._request(
            "energyprices",
            params={
                "fromDate": self.to_datetime_string(start_date),
                "tillDate": self.to_datetime_string(
                    end_date,
                    timedelta(hours=23, minutes=59, seconds=59, milliseconds=999),
                ),
                "interval": interval,
                "usageType": 1,
                "inclBtw": vat.value if vat is not None else VatOption.INCLUDE.value,
            },
        )

        if data["Prices"] == []:
            msg = "No energy prices found for this period."
            raise EnergyZeroNoDataError(msg)
        return Electricity.from_dict(data)

    async def get_gas_prices(
        self,
        start_date: date,
        end_date: date,
        price_type: PriceType = PriceType.ALL_IN,
    ) -> EnergyPrices:
        """Get gas prices for a given period.

        Uses the EnergyZero GraphQL API for more accurate results.
        Can also return all-in prices.

        Args:
        ----
            start_date: Start date of the period. Local timezone.
            end_date: End date of the period. Local timezone.
            price_type:
                PriceType.ALL_IN: return prices including energy tax,
                    VAT and purchasing cost. This is how much a
                    consumer would actually pay.
                PriceType.MARKET: return the raw market prices,
                    excluding taxes and purchase fees

        Returns:
        -------
            A Python dictionary with the response from EnergyZero.

        Raises:
        ------
            EnergyZeroNoDataError: No energy prices found for this period.

        """
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

        # Gas prices are valid from 06:00 to 06:00 the next day, so to make sure
        # we include gas prices for the entire specified date range
        # (start_date 00:00 to end_date 23:59:59), we need to also include parts
        # of the day before and the day after the specified range:

        from_str = self.to_datetime_string(start_date, timedelta(hours=6, days=-1))
        till_str = self.to_datetime_string(end_date, timedelta(hours=6, days=1))

        data = await self._request(
            "gql",
            method=METH_POST,
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
            raise EnergyZeroNoDataError(msg)

        return EnergyPrices.from_dict(data["data"], price_type)

    async def get_electricity_prices(
        self,
        start_date: date,
        end_date: date,
        price_type: PriceType = PriceType.ALL_IN,
    ) -> EnergyPrices:
        """Get electricity prices for a given period.

        Uses the EnergyZero GraphQL API for more accurate results.
        Can also return all-in prices.

        Args:
        ----
            start_date: Start date of the period. Local timezone.
            end_date: End date of the period. Local timezone.
            price_type:
                PriceType.ALL_IN: return prices including energy tax,
                    VAT and purchasing cost. This is how much a
                    consumer would actually pay.
                PriceType.MARKET: return the raw market prices,
                    excluding taxes and purchase fees

        Returns:
        -------
            A Python dictionary with the response from EnergyZero.

        Raises:
        ------
            EnergyZeroNoDataError: No energy prices found for this period.

        """
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
            method=METH_POST,
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
            raise EnergyZeroNoDataError(msg)

        return EnergyPrices.from_dict(data["data"], price_type)

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

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
