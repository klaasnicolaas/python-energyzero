"""Test the models."""

from datetime import UTC, date, datetime

import pytest
from aiohttp import ClientSession
from aresponses import ResponsesMockServer
from syrupy.assertion import SnapshotAssertion

from energyzero import Electricity, EnergyZero, EnergyZeroNoDataError, Gas, VatOption

from . import load_fixtures


@pytest.mark.freeze_time("2022-12-07 15:00:00+01:00")
async def test_electricity_model(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the electricity model at 15:00:00 CET."""
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
    async with ClientSession() as session:
        today = date(2022, 12, 7)
        client = EnergyZero(session=session)
        energy: Electricity = await client.energy_prices(
            start_date=today,
            end_date=today,
            vat=VatOption.INCLUDE,
        )

        assert energy == snapshot
        assert isinstance(energy, Electricity)
        assert isinstance(energy.timestamp_prices, list)

        assert energy.extreme_prices[1] == 0.55
        assert energy.extreme_prices[0] == 0.26
        assert energy.average_price == 0.37
        assert energy.current_price == 0.48
        assert energy.pct_of_max_price == 87.27
        assert energy.hours_priced_equal_or_lower == 23

        # The next hour price
        next_hour = datetime(2022, 12, 7, 15, 0, tzinfo=UTC)
        assert energy.price_at_time(next_hour) == 0.49
        assert energy.lowest_price_time == datetime.strptime(
            "2022-12-07 02:00",
            "%Y-%m-%d %H:%M",
        ).replace(tzinfo=UTC)
        assert energy.highest_price_time == datetime.strptime(
            "2022-12-07 16:00",
            "%Y-%m-%d %H:%M",
        ).replace(tzinfo=UTC)


async def test_electricity_none_date(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
) -> None:
    """Test when there is no data for the current datetime."""
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
    async with ClientSession() as session:
        today = date(2022, 12, 7)
        client = EnergyZero(session=session)
        energy: Electricity = await client.energy_prices(
            start_date=today,
            end_date=today,
            vat=VatOption.INCLUDE,
        )

        assert energy == snapshot
        assert isinstance(energy, Electricity)
        assert energy.current_price is None


@pytest.mark.freeze_time("2022-12-07 00:30:00+02:00")
async def test_electricity_midnight_cest(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the electricity model between 00:00 and 01:00 with in CEST."""
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
    async with ClientSession() as session:
        today = date(2022, 12, 7)
        client = EnergyZero(session=session)
        energy: Electricity = await client.energy_prices(
            start_date=today,
            end_date=today,
            vat=VatOption.INCLUDE,
        )

        assert energy == snapshot
        assert isinstance(energy, Electricity)
        # Price at 22:30:00 UTC
        assert energy.current_price == 0.31


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
    async with ClientSession() as session:
        today = date(2022, 12, 7)
        client = EnergyZero(session=session)
        with pytest.raises(EnergyZeroNoDataError):
            await client.energy_prices(start_date=today, end_date=today)


@pytest.mark.freeze_time("2022-12-07 15:00:00+01:00")
async def test_gas_model(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the gas model at 15:00:00 CET."""
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
    async with ClientSession() as session:
        today = date(2022, 12, 7)
        client = EnergyZero(session=session)
        gas: Gas = await client.gas_prices(
            start_date=today,
            end_date=today,
            vat=VatOption.INCLUDE,
        )

        assert gas == snapshot
        assert isinstance(gas, Gas)
        assert isinstance(gas.timestamp_prices, list)

        assert gas.extreme_prices[1] == 1.47
        assert gas.extreme_prices[0] == 1.43

        # The next hour price
        next_hour = datetime(2022, 12, 7, 15, 0, tzinfo=UTC)
        assert gas.price_at_time(next_hour) == 1.47


@pytest.mark.freeze_time("2022-12-07 04:00:00+01:00")
async def test_gas_morning_model(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the gas model in the morning at 04:00:00 CET."""
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
    async with ClientSession() as session:
        today = date(2022, 12, 7)
        client = EnergyZero(session=session)
        gas: Gas = await client.gas_prices(
            start_date=today, end_date=today, vat=VatOption.INCLUDE
        )

        assert gas == snapshot
        assert isinstance(gas, Gas)


async def test_gas_none_date(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
) -> None:
    """Test when there is no data for the current datetime."""
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
    async with ClientSession() as session:
        today = date(2022, 12, 7)
        client = EnergyZero(session=session)
        gas: Gas = await client.gas_prices(start_date=today, end_date=today)

        assert gas == snapshot
        assert isinstance(gas, Gas)
        assert gas.current_price is None


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
    async with ClientSession() as session:
        today = date(2022, 12, 7)
        client = EnergyZero(session=session)
        with pytest.raises(EnergyZeroNoDataError):
            await client.gas_prices(start_date=today, end_date=today)
