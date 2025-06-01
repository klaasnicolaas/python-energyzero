"""Test the models."""

from datetime import UTC, date, datetime, time

import pytest
from aresponses import ResponsesMockServer
from syrupy.assertion import SnapshotAssertion

from energyzero import (
    Electricity,
    EnergyPrices,
    EnergyZero,
    EnergyZeroNoDataError,
    Gas,
    PriceType,
    TimeRange,
    VatOption,
)

from . import load_fixtures


@pytest.mark.freeze_time("2022-12-07 15:00:00+01:00")
async def test_electricity_model(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    energyzero_client: EnergyZero,
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
    today = date(2022, 12, 7)
    energy: Electricity = await energyzero_client.energy_prices(
        start_date=today,
        end_date=today,
        vat=VatOption.INCLUDE,
    )
    assert energy == snapshot
    assert isinstance(energy, Electricity)
    assert isinstance(energy.timestamp_prices, list)

    # Electricity prices
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
    energyzero_client: EnergyZero,
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
    today = date(2022, 12, 7)
    energy: Electricity = await energyzero_client.energy_prices(
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
    energyzero_client: EnergyZero,
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
    today = date(2022, 12, 7)
    energy: Electricity = await energyzero_client.energy_prices(
        start_date=today,
        end_date=today,
        vat=VatOption.INCLUDE,
    )
    assert energy == snapshot
    assert isinstance(energy, Electricity)
    # Price at 22:30:00 UTC
    assert energy.current_price == 0.31


async def test_no_electricity_data(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
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
    today = date(2022, 12, 7)
    with pytest.raises(EnergyZeroNoDataError):
        await energyzero_client.energy_prices(start_date=today, end_date=today)


@pytest.mark.freeze_time("2022-12-07 15:00:00+01:00")
async def test_gas_model(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    energyzero_client: EnergyZero,
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
    today = date(2022, 12, 7)
    gas: Gas = await energyzero_client.gas_prices(
        start_date=today, end_date=today, vat=VatOption.INCLUDE
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
    energyzero_client: EnergyZero,
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
    today = date(2022, 12, 7)
    gas: Gas = await energyzero_client.gas_prices(
        start_date=today, end_date=today, vat=VatOption.INCLUDE
    )
    assert gas == snapshot
    assert isinstance(gas, Gas)
    assert isinstance(gas.timestamp_prices, list)


async def test_gas_none_date(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    energyzero_client: EnergyZero,
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
    today = date(2022, 12, 7)
    gas: Gas = await energyzero_client.gas_prices(
        start_date=today, end_date=today, vat=VatOption.INCLUDE
    )
    assert gas == snapshot
    assert isinstance(gas, Gas)
    assert gas.current_price is None


async def test_no_gas_data(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
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
    today = date(2022, 12, 7)
    with pytest.raises(EnergyZeroNoDataError):
        await energyzero_client.gas_prices(start_date=today, end_date=today)


############################################################################
## GraphQL API model tests                                                ##
############################################################################


@pytest.mark.freeze_time("2025-05-31 15:00:00+01:00")
async def test_electricity_ex_model(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    energyzero_client: EnergyZero,
) -> None:
    """Test the electricity model at 15:00:00 CET."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("energy_ex.json"),
        ),
    )
    today = date(2025, 5, 31)
    energy: EnergyPrices = await energyzero_client.electricity_prices_ex(
        start_date=today,
        end_date=today,
        price_type=PriceType.ALL_IN,
    )
    assert energy == snapshot
    assert isinstance(energy, EnergyPrices)
    assert isinstance(energy.timestamp_prices, list)

    # Electricity prices
    assert energy.extreme_prices is not None
    assert energy.extreme_prices[1] == 0.3895111
    assert energy.extreme_prices[0] == 0.1408077
    assert energy.average_price == 0.24064782499999993
    assert energy.current_price == 0.1566829
    assert energy.pct_of_max_price == 40.23
    assert energy.hours_priced_equal_or_lower == 6

    # The next hour price
    next_hour = datetime(2025, 5, 31, 15, 0, tzinfo=UTC)
    assert energy.price_at_time(next_hour) == 0.20090840000000001
    assert energy.lowest_price_time_range == TimeRange(
        datetime.combine(today, time(11, 0, 0), UTC),
        datetime.combine(today, time(12, 0, 0), UTC),
    )
    assert energy.highest_price_time_range == TimeRange(
        datetime.combine(today, time(19, 0, 0), UTC),
        datetime.combine(today, time(20, 0, 0), UTC),
    )


@pytest.mark.freeze_time("2025-01-01 00:30:00+01:00")
async def test_electricity_ex_none_date(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    energyzero_client: EnergyZero,
) -> None:
    """Test when there is no data for the current datetime."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("energy_ex.json"),
        ),
    )
    today = date(2025, 5, 31)
    energy: EnergyPrices = await energyzero_client.electricity_prices_ex(
        start_date=today,
        end_date=today,
        price_type=PriceType.ALL_IN,
    )
    assert energy == snapshot
    assert isinstance(energy, EnergyPrices)
    assert energy.current_price is None


@pytest.mark.freeze_time("2025-05-31 00:30:00+01:00")
async def test_electricity_ex_midnight_cest(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    energyzero_client: EnergyZero,
) -> None:
    """Test the electricity model between 00:00 and 01:00 with in CEST."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("energy_ex.json"),
        ),
    )
    today = date(2025, 5, 31)
    energy: EnergyPrices = await energyzero_client.electricity_prices_ex(
        start_date=today,
        end_date=today,
        price_type=PriceType.ALL_IN,
    )
    assert energy == snapshot
    assert isinstance(energy, EnergyPrices)
    # Price at 22:30:00 UTC
    assert energy.current_price == 0.2749604


async def test_no_electricity_ex_data(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Raise exception when there is no data."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("no_data_ex.json"),
        ),
    )
    today = date(2025, 5, 31)
    with pytest.raises(EnergyZeroNoDataError):
        await energyzero_client.electricity_prices_ex(start_date=today, end_date=today)


@pytest.mark.freeze_time("2025-05-31 15:00:00+01:00")
async def test_gas_ex_model(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    energyzero_client: EnergyZero,
) -> None:
    """Test the gas model at 15:00:00 CET."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("gas_ex.json"),
        ),
    )
    today = date(2025, 5, 31)
    gas: EnergyPrices = await energyzero_client.gas_prices_ex(
        start_date=today, end_date=today, price_type=PriceType.ALL_IN
    )

    assert gas == snapshot
    assert isinstance(gas, EnergyPrices)
    assert isinstance(gas.timestamp_prices, list)

    assert gas.extreme_prices is not None
    assert gas.extreme_prices[1] == 1.21367051296348
    assert gas.extreme_prices[0] == 1.19915429151276

    # The next hour price
    next_hour = datetime(2025, 5, 31, 15, 0, tzinfo=UTC)
    assert gas.price_at_time(next_hour) == 1.19915429151276


@pytest.mark.freeze_time("2025-05-31 04:00:00+01:00")
async def test_gas_ex_morning_model(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    energyzero_client: EnergyZero,
) -> None:
    """Test the gas model in the morning at 04:00:00 CET."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("gas_ex.json"),
        ),
    )
    today = date(2025, 5, 31)
    gas: EnergyPrices = await energyzero_client.gas_prices_ex(
        start_date=today,
        end_date=today,
        price_type=PriceType.ALL_IN,
    )
    assert gas == snapshot
    assert isinstance(gas, EnergyPrices)
    assert isinstance(gas.timestamp_prices, list)


@pytest.mark.freeze_time("2025-01-01 00:30:00+01:00")
async def test_gas_ex_none_date(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    energyzero_client: EnergyZero,
) -> None:
    """Test when there is no data for the current datetime."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("gas_ex.json"),
        ),
    )
    today = date(2025, 5, 31)
    gas: EnergyPrices = await energyzero_client.gas_prices_ex(
        start_date=today,
        end_date=today,
        price_type=PriceType.ALL_IN,
    )
    assert gas == snapshot
    assert isinstance(gas, EnergyPrices)
    assert gas.current_price is None


async def test_no_gas_ex_data(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Raise exception when there is no data."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("no_data_ex.json"),
        ),
    )
    today = date(2025, 5, 31)
    with pytest.raises(EnergyZeroNoDataError):
        await energyzero_client.gas_prices_ex(start_date=today, end_date=today)
