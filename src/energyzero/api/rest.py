"""REST API client for EnergyZero."""

from __future__ import annotations

import asyncio
import json
import socket
from dataclasses import dataclass
from importlib import metadata
from typing import TYPE_CHECKING, Any

from aiohttp.client import ClientError, ClientSession
from aiohttp.hdrs import METH_GET
from yarl import URL

from energyzero.const import Interval, PriceType
from energyzero.exceptions import (
    EnergyZeroConnectionError,
    EnergyZeroError,
    EnergyZeroNoDataError,
)
from energyzero.models import EnergyPrices

if TYPE_CHECKING:
    from datetime import date

VERSION = metadata.version("energyzero")


@dataclass
class RESTClient:
    """REST API client for EnergyZero."""

    request_timeout: float = 10.0
    session: ClientSession | None = None

    _close_session: bool = False

    async def _request(
        self,
        uri: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Handle a request to the REST API.

        Args:
        ----
            uri: Request URI path.
            params: Query parameters.

        Returns:
        -------
            A Python dictionary with the response.

        Raises:
        ------
            EnergyZeroConnectionError: Connection error.
            EnergyZeroError: Unexpected response.

        """
        url = URL.build(
            scheme="https",
            host="public.api.energyzero.nl",
            path=f"/{uri}",
        )

        headers = {
            "Accept": "application/json",
            "User-Agent": f"PythonEnergyZero/{VERSION}",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(
                    METH_GET,
                    url,
                    params=params,
                    headers=headers,
                    ssl=True,
                )
        except TimeoutError as exception:
            msg = "Timeout occurred while connecting to the API."
            raise EnergyZeroConnectionError(message=msg) from exception
        except (ClientError, socket.gaierror) as exception:
            msg = "Error occurred while communicating with the API."
            raise EnergyZeroConnectionError(message=msg) from exception

        text = await response.text()

        error_payload: dict[str, Any] | None = None
        if text:
            try:
                error_payload = json.loads(text)
            except json.JSONDecodeError:
                error_payload = None

        if response.status == 404:
            raise EnergyZeroNoDataError(
                data=error_payload,
                status=response.status,
            )

        if response.status >= 400:
            raise EnergyZeroConnectionError(
                data=error_payload,
                status=response.status,
            )

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            msg = "Unexpected content type response from the REST API"
            raise EnergyZeroError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        return json.loads(text)

    async def get_electricity_prices(
        self,
        start_date: date,
        end_date: date | None = None,
        interval: Interval | str = Interval.QUARTER,
        price_type: PriceType = PriceType.ALL_IN,
    ) -> EnergyPrices:
        """Get electricity prices using REST API.

        Args:
        ----
            start_date: Start date (local timezone).
            end_date: Optional end date. REST API supports single-day requests
                only; when provided it must match ``start_date``.
            interval: INTERVAL_QUARTER (15 min) or INTERVAL_HOUR.
            price_type: ALL_IN or MARKET prices.

        Returns:
        -------
            An EnergyPrices object.

        Raises:
        ------
            EnergyZeroNoDataError: No data found.

        """
        if end_date and end_date != start_date:
            msg = "REST API supports single-day requests. Use identical dates."
            raise ValueError(msg)

        date_str = start_date.strftime("%d-%m-%Y")

        interval_value = interval.value if isinstance(interval, Interval) else interval

        data = await self._request(
            "public/v1/prices",
            params={
                "energyType": "ENERGY_TYPE_ELECTRICITY",
                "date": date_str,
                "interval": interval_value,
            },
        )

        if not data or len(data.get("base", [])) == 0:
            msg = "No electricity prices found for this period."
            raise EnergyZeroNoDataError(message=msg)

        prices = EnergyPrices.from_rest_dict(
            data,
            price_type,
            filter_date=start_date,
        )

        if len(prices.prices) == 0:
            msg = f"No electricity prices found for {start_date}"
            raise EnergyZeroNoDataError(message=msg)

        return prices

    async def get_gas_prices(
        self,
        start_date: date,
        end_date: date | None = None,
        price_type: PriceType = PriceType.ALL_IN,
    ) -> EnergyPrices:
        """Get gas prices using REST API.

        Args:
        ----
            start_date: Start date (local timezone).
            end_date: Optional end date. REST API supports single-day requests
                only; when provided it must match ``start_date``.
            price_type: ALL_IN or MARKET prices.

        Returns:
        -------
            An EnergyPrices object.

        Raises:
        ------
            EnergyZeroNoDataError: No data found.

        """
        if end_date and end_date != start_date:
            msg = "REST API supports single-day requests. Use identical dates."
            raise ValueError(msg)

        date_str = start_date.strftime("%d-%m-%Y")

        data = await self._request(
            "public/v1/prices",
            params={
                "energyType": "ENERGY_TYPE_GAS",
                "date": date_str,
                "interval": "INTERVAL_DAY",
            },
        )

        if not data or len(data.get("base", [])) == 0:
            msg = "No gas prices found for this period."
            raise EnergyZeroNoDataError(message=msg)

        prices = EnergyPrices.from_rest_dict(
            data,
            price_type,
            filter_date=start_date,
        )

        if len(prices.prices) == 0:
            msg = f"No gas prices found for {start_date}"
            raise EnergyZeroNoDataError(message=msg)

        return prices

    async def close(self) -> None:
        """Close the client session."""
        if self.session and self._close_session:
            await self.session.close()
