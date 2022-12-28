"""Test the models."""
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from energyzero import Electricity, EnergyZero, EnergyZeroNoDataError, Gas

from . import load_fixtures


@pytest.mark.asyncio
@patch(
    "energyzero.models.Electricity.utcnow",
    Mock(return_value=datetime(2022, 12, 7, 14, 0).replace(tzinfo=timezone.utc)),
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
        assert energy.extreme_prices[1] == 0.55
        assert energy.extreme_prices[0] == 0.26
        assert energy.average_price == 0.37
        assert energy.current_price == 0.48
        # The next hour price
        next_hour = datetime(2022, 12, 7, 15, 0).replace(tzinfo=timezone.utc)
        assert energy.price_at_time(next_hour) == 0.49
        assert energy.lowest_price_time == datetime.strptime(
            "2022-12-07 02:00", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=timezone.utc)
        assert energy.highest_price_time == datetime.strptime(
            "2022-12-07 16:00", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=timezone.utc)
        assert energy.pct_of_max_price == 87.27
        assert isinstance(energy.timestamp_prices, list)


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
        with pytest.raises(EnergyZeroNoDataError):
            await client.energy_prices(start_date=today, end_date=today)


@pytest.mark.asyncio
@patch(
    "energyzero.models.Gas.utcnow",
    Mock(return_value=datetime(2022, 12, 7, 14, 0).replace(tzinfo=timezone.utc)),
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
        today = datetime.strptime("2022-12-07", "%Y-%m-%d")
        client = EnergyZero(session=session)
        gas: Gas = await client.gas_prices(start_date=today, end_date=today)
        assert gas is not None and isinstance(gas, Gas)
        assert gas.extreme_prices[1] == 1.47
        assert gas.extreme_prices[0] == 1.43
        assert gas.average_price == 1.45
        assert gas.current_price == 1.47
        # The next hour price
        next_hour = datetime(2022, 12, 7, 15, 0).replace(tzinfo=timezone.utc)
        assert gas.price_at_time(next_hour) == 1.47


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
        with pytest.raises(EnergyZeroNoDataError):
            await client.gas_prices(start_date=today, end_date=today)
