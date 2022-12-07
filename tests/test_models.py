"""Test the models."""
from datetime import datetime, timezone
from unittest import mock

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from energyzero import Electricity, EnergyZero, EnergyZeroError, Gas

from . import load_fixtures


@pytest.mark.asyncio
@mock.patch(
    "energyzero.models._now",
    return_value=datetime.strptime("2022-12-07 13:00", "%Y-%m-%d %H:%M").replace(
        tzinfo=timezone.utc
    ),
)
async def test_electricity_model(aresponses: ResponsesMockServer) -> None:
    """Test the electricity model."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/energyprices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("energy.json"),
        ),
    )
    async with aiohttp.ClientSession() as session:
        today = datetime.strptime("2022-12-07", "%Y-%m-%d")
        client = EnergyZero(session=session)
        energy: Electricity = await client.energy_prices(
            start_date=today, end_date=today
        )
        assert energy is not None and isinstance(energy, Electricity)
        assert energy.max_price == 0.55
        assert energy.min_price == 0.26
        assert energy.average_price == 0.37
        assert energy.current_hourprice == 0.44
        assert energy.next_hourprice == 0.48
        assert energy.min_price_time == datetime.strptime(
            "2022-12-07 02:00", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=timezone.utc)
        assert energy.max_price_time == datetime.strptime(
            "2022-12-07 16:00", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_no_electricity_data(aresponses: ResponsesMockServer) -> None:
    """Raise exception when there is no data."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/energyprices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("no_data.json"),
        ),
    )
    async with aiohttp.ClientSession() as session:
        today = datetime.strptime("2022-12-07", "%Y-%m-%d")
        client = EnergyZero(session=session)
        with pytest.raises(EnergyZeroError):
            await client.energy_prices(start_date=today, end_date=today)


@pytest.mark.asyncio
@mock.patch(
    "energyzero.models._now",
    return_value=datetime.strptime("2022-12-05 13:00", "%Y-%m-%d %H:%M").replace(
        tzinfo=timezone.utc
    ),
)
async def test_gas_model(aresponses: ResponsesMockServer) -> None:
    """Test the gas model."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/energyprices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("gas.json"),
        ),
    )
    async with aiohttp.ClientSession() as session:
        today = datetime.strptime("2022-12-05", "%Y-%m-%d")
        client = EnergyZero(session=session)
        gas: Gas = await client.gas_prices(start_date=today, end_date=today)
        assert gas is not None and isinstance(gas, Gas)
        assert gas.max_price == 1.43
        assert gas.min_price == 1.42
        assert gas.average_price == 1.42
        assert gas.current_hourprice == 1.43
        assert gas.next_hourprice == 1.43


@pytest.mark.asyncio
async def test_no_gas_data(aresponses: ResponsesMockServer) -> None:
    """Raise exception when there is no data."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/energyprices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("no_data.json"),
        ),
    )
    async with aiohttp.ClientSession() as session:
        today = datetime.strptime("2022-12-07", "%Y-%m-%d")
        client = EnergyZero(session=session)
        with pytest.raises(EnergyZeroError):
            await client.gas_prices(start_date=today, end_date=today)
