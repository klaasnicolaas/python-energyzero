"""Asynchronous Python client for the EnergyZero API."""
from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from importlib import metadata
from typing import Any

import aiohttp
import async_timeout
from aiohttp import hdrs
from yarl import URL

from .exceptions import (
    EnergyZeroConnectionError,
    EnergyZeroError,
    EnergyZeroNoDataError,
)
from .models import Electricity, Gas


def get_utcnow() -> datetime:
    """Get the current UTC time.

    Returns:
        The current UTC time.
    """
    return datetime.now(timezone.utc)


@dataclass
class EnergyZero:
    """Main class for handling data fetching from EnergyZero."""

    incl_btw: str = "true"
    request_timeout: float = 10.0
    session: aiohttp.client.ClientSession | None = None

    _close_session: bool = False

    async def _request(
        self,
        uri: str,
        *,
        method: str = hdrs.METH_GET,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Handle a request to the API of EnergyZero.

        Args:
            uri: Request URI, without '/', for example, 'status'
            method: HTTP method to use, for example, 'GET'
            params: Extra options to improve or limit the response.

        Returns:
            A Python dictionary (json) with the response from EnergyZero.

        Raises:
            EnergyZeroConnectionError: An error occurred while
                communicating with the API.
            EnergyZeroError: Received an unexpected response from
                the API.
        """
        version = metadata.version(__package__)
        url = URL.build(scheme="https", host="api.energyzero.nl", path="/v1/").join(
            URL(uri)
        )

        headers = {
            "Accept": "application/json, text/plain",
            "User-Agent": f"PythonEnergyZero/{version}",
        }

        if self.session is None:
            self.session = aiohttp.ClientSession()
            self._close_session = True

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    ssl=True,
                )
                response.raise_for_status()
        except asyncio.TimeoutError as exception:
            raise EnergyZeroConnectionError(
                "Timeout occurred while connecting to the API."
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise EnergyZeroConnectionError(
                "Error occurred while communicating with the API."
            ) from exception

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            text = await response.text()
            raise EnergyZeroError(
                "Unexpected content type response from the EnergyZero API",
                {"Content-Type": content_type, "response": text},
            )

        return await response.json()

    async def gas_prices(
        self, start_date: date, end_date: date, interval: int = 4
    ) -> Gas:
        """Get gas prices for a given period.

        Args:
            start_date: Start date of the period.
            end_date: End date of the period.
            interval: Interval of the prices.

        Returns:
            A Python dictionary with the response from EnergyZero.

        Raises:
            EnergyZeroNoDataError: No gas prices found for this period.
        """
        start_date_utc: datetime
        end_date_utc: datetime
        if get_utcnow().hour >= 5 and get_utcnow().hour <= 22:
            # Set start_date to 05:00:00 and the end_date to 04:59:59 UTC next day
            start_date_utc = datetime(
                start_date.year, start_date.month, start_date.day, 5, 0, 0
            )
            end_date_utc = datetime(
                end_date.year, end_date.month, end_date.day, 4, 59, 59
            ) + timedelta(days=1)
        else:
            # Set start_date to 05:00:00 prev day and the end_date to 04:59:59 UTC
            start_date_utc = datetime(
                start_date.year, start_date.month, start_date.day, 5, 0, 0
            ) - timedelta(days=1)
            end_date_utc = datetime(
                end_date.year, end_date.month, end_date.day, 4, 59, 59
            )

        data = await self._request(
            "energyprices",
            params={
                "fromDate": start_date_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "tillDate": end_date_utc.strftime("%Y-%m-%dT%H:%M:%S.999Z"),
                "interval": interval,
                "usageType": 3,
                "inclBtw": self.incl_btw.lower(),
            },
        )

        if data["Prices"] == []:
            raise EnergyZeroNoDataError("No gas prices found for this period.")
        return Gas.from_dict(data)

    async def energy_prices(
        self, start_date: date, end_date: date, interval: int = 4
    ) -> Electricity:
        """Get energy prices for a given period.

        Args:
            start_date: Start date of the period.
            end_date: End date of the period.
            interval: Interval of the prices.

        Returns:
            A Python dictionary with the response from EnergyZero.

        Raises:
            EnergyZeroNoDataError: No energy prices found for this period.
        """
        # Set the start date to 23:00:00 previous day and the end date to 22:59:59 UTC
        start_date_utc: datetime = datetime(
            start_date.year, start_date.month, start_date.day, 0, 0, 0
        ) - timedelta(hours=1)
        end_date_utc: datetime = datetime(
            end_date.year, end_date.month, end_date.day, 22, 59, 59
        )
        data = await self._request(
            "energyprices",
            params={
                "fromDate": start_date_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "tillDate": end_date_utc.strftime("%Y-%m-%dT%H:%M:%S.999Z"),
                "interval": interval,
                "usageType": 1,
                "inclBtw": self.incl_btw.lower(),
            },
        )

        if data["Prices"] == []:
            raise EnergyZeroNoDataError("No energy prices found for this period.")
        return Electricity.from_dict(data)

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> EnergyZero:
        """Async enter.

        Returns:
            The EnergyZero object.
        """
        return self

    async def __aexit__(self, *_exc_info: Any) -> None:
        """Async exit.

        Args:
            _exc_info: Exec type.
        """
        await self.close()
