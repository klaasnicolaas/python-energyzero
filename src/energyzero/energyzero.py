"""Asynchronous Python client for the EnergyZero API."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from importlib import metadata
from typing import Any, Self, cast

from aiohttp.client import ClientError, ClientSession
from aiohttp.hdrs import METH_GET
from yarl import URL

from .const import VatOption
from .exceptions import (
    EnergyZeroConnectionError,
    EnergyZeroError,
    EnergyZeroNoDataError,
)
from .models import Electricity, Gas

VERSION = metadata.version(__package__)


@dataclass
class EnergyZero:
    """Main class for handling data fetching from EnergyZero."""

    vat: VatOption = VatOption.INCLUDE
    request_timeout: float = 10.0
    session: ClientSession | None = None

    _close_session: bool = False

    async def _request(
        self,
        uri: str,
        *,
        method: str = METH_GET,
        params: dict[str, Any] | None = None,
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

        return cast(dict[str, Any], await response.json())

    async def gas_prices(
        self,
        start_date: date,
        end_date: date,
        interval: int = 4,
        vat: VatOption | None = None,
    ) -> Gas:
        """Get gas prices for a given period.

        Args:
        ----
            start_date: Start date of the period.
            end_date: End date of the period.
            interval: Interval of the prices.
            vat: VAT category.

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
            utc_start_date = datetime(
                start_date.year,
                start_date.month,
                start_date.day,
                6,
                0,
                0,
                tzinfo=local_tz,
            ).astimezone(UTC)
            utc_end_date = datetime(
                end_date.year,
                end_date.month,
                end_date.day,
                5,
                59,
                59,
                tzinfo=local_tz,
            ).astimezone(UTC) + timedelta(days=1)
        else:
            # Set start_date to 06:00:00 prev day and the end_date to 05:59:59
            # Convert to UTC time 04:00:00 prev day and 03:59:59 current day
            utc_start_date = datetime(
                start_date.year,
                start_date.month,
                start_date.day,
                6,
                0,
                0,
                tzinfo=local_tz,
            ).astimezone(UTC) - timedelta(days=1)
            utc_end_date = datetime(
                end_date.year,
                end_date.month,
                end_date.day,
                5,
                59,
                59,
                tzinfo=local_tz,
            ).astimezone(UTC)
        data = await self._request(
            "energyprices",
            params={
                "fromDate": utc_start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "tillDate": utc_end_date.strftime("%Y-%m-%dT%H:%M:%S.999Z"),
                "interval": interval,
                "usageType": 3,
                "inclBtw": vat.value if vat is not None else self.vat.value,
            },
        )

        if data["Prices"] == []:
            msg = "No gas prices found for this period."
            raise EnergyZeroNoDataError(msg)
        return Gas.from_dict(data)

    async def energy_prices(
        self,
        start_date: date,
        end_date: date,
        interval: int = 4,
        vat: VatOption | None = None,
    ) -> Electricity:
        """Get energy prices for a given period.

        Args:
        ----
            start_date: Start date of the period.
            end_date: End date of the period.
            interval: Interval of the prices.
            vat: VAT category.

        Returns:
        -------
            A Python dictionary with the response from EnergyZero.

        Raises:
        ------
            EnergyZeroNoDataError: No energy prices found for this period.

        """
        local_tz = datetime.now(UTC).astimezone().tzinfo
        # Set start_date to 00:00:00 and the end_date to 23:59:59 and convert to UTC
        utc_start_date = datetime(
            start_date.year,
            start_date.month,
            start_date.day,
            0,
            0,
            0,
            tzinfo=local_tz,
        ).astimezone(UTC)
        utc_end_date = datetime(
            end_date.year,
            end_date.month,
            end_date.day,
            23,
            59,
            59,
            tzinfo=local_tz,
        ).astimezone(UTC)
        data = await self._request(
            "energyprices",
            params={
                "fromDate": utc_start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "tillDate": utc_end_date.strftime("%Y-%m-%dT%H:%M:%S.999Z"),
                "interval": interval,
                "usageType": 1,
                "inclBtw": vat.value if vat is not None else self.vat.value,
            },
        )

        if data["Prices"] == []:
            msg = "No energy prices found for this period."
            raise EnergyZeroNoDataError(msg)
        return Electricity.from_dict(data)

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
