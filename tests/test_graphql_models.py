"""Test GraphQL API models for EnergyZero."""

from datetime import UTC, date, datetime, time, timedelta, timezone
from json import loads

import pytest
from aresponses import ResponsesMockServer
from syrupy.assertion import SnapshotAssertion

from energyzero import (
    EnergyPrices,
    EnergyZero,
    EnergyZeroNoDataError,
    PriceType,
    TimeRange,
)

from . import load_fixtures

############################################################################
## GraphQL API model tests                                                ##
############################################################################


@pytest.mark.freeze_time("2025-05-31 15:00:00+01:00")
async def test_graphql_electricity_model(
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
            text=load_fixtures("graphql/energy.json"),
        ),
    )
    today = date(2025, 5, 31)
    energy: EnergyPrices = await energyzero_client.get_electricity_prices(
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
    assert energy.time_ranges_priced_equal_or_lower == 6

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
async def test_graphql_electricity_none_date(
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
            text=load_fixtures("graphql/energy.json"),
        ),
    )
    today = date(2025, 5, 31)
    energy: EnergyPrices = await energyzero_client.get_electricity_prices(
        start_date=today,
        end_date=today,
        price_type=PriceType.ALL_IN,
    )
    assert energy == snapshot
    assert isinstance(energy, EnergyPrices)
    assert energy.current_price is None


@pytest.mark.freeze_time("2025-05-31 00:30:00+01:00")
async def test_graphql_electricity_midnight_cest(
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
            text=load_fixtures("graphql/energy.json"),
        ),
    )
    today = date(2025, 5, 31)
    energy: EnergyPrices = await energyzero_client.get_electricity_prices(
        start_date=today,
        end_date=today,
        price_type=PriceType.ALL_IN,
    )
    assert energy == snapshot
    assert isinstance(energy, EnergyPrices)
    # Price at 22:30:00 UTC
    assert energy.current_price == 0.2749604


async def test_graphql_no_electricity_data(
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
            text=load_fixtures("graphql/no_data.json"),
        ),
    )
    today = date(2025, 5, 31)
    with pytest.raises(EnergyZeroNoDataError):
        await energyzero_client.get_electricity_prices(start_date=today, end_date=today)


@pytest.mark.freeze_time("2025-05-31 15:00:00+01:00")
async def test_graphql_gas_model(
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
            text=load_fixtures("graphql/gas.json"),
        ),
    )
    today = date(2025, 5, 31)
    gas: EnergyPrices = await energyzero_client.get_gas_prices(
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
async def test_graphql_gas_morning_model(
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
            text=load_fixtures("graphql/gas.json"),
        ),
    )
    today = date(2025, 5, 31)
    gas: EnergyPrices = await energyzero_client.get_gas_prices(
        start_date=today,
        end_date=today,
        price_type=PriceType.ALL_IN,
    )
    assert gas == snapshot
    assert isinstance(gas, EnergyPrices)
    assert isinstance(gas.timestamp_prices, list)


@pytest.mark.freeze_time("2025-01-01 00:30:00+01:00")
async def test_graphql_gas_none_date(
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
            text=load_fixtures("graphql/gas.json"),
        ),
    )
    today = date(2025, 5, 31)
    gas: EnergyPrices = await energyzero_client.get_gas_prices(
        start_date=today,
        end_date=today,
        price_type=PriceType.ALL_IN,
    )
    assert gas == snapshot
    assert isinstance(gas, EnergyPrices)
    assert gas.current_price is None


async def test_graphql_no_gas_data(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Test if a response without any data throws the correct exception."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("graphql/no_data.json"),
        ),
    )
    today = date(2025, 5, 31)
    with pytest.raises(EnergyZeroNoDataError):
        await energyzero_client.get_gas_prices(start_date=today, end_date=today)


async def test_timerange_astimezone() -> None:
    """Test if astimezone returns the correct new time range."""
    tz_from = timezone.min
    tz_to = timezone.max
    range_start = datetime.now(tz=tz_from)
    range_end = range_start + timedelta(hours=6)

    range_from_tz = TimeRange(range_start, range_end)
    range_to_tz = range_from_tz.astimezone(tz_to)

    assert range_from_tz.start_including.tzinfo == tz_from
    assert range_from_tz.end_excluding.tzinfo == tz_from
    assert range_to_tz.start_including.tzinfo == tz_to
    assert range_to_tz.end_excluding.tzinfo == tz_to


async def test_timerange_str() -> None:
    """Test if the string representation for a TimeRange is correct."""
    range_from_tz = TimeRange(
        datetime(year=2025, month=1, day=2, hour=10, minute=9, second=8, tzinfo=UTC),
        datetime(year=2025, month=3, day=4, hour=7, minute=6, second=5, tzinfo=UTC),
    )

    assert f"{range_from_tz}" == "2025-01-02 10:09:08 - 2025-03-04 07:06:05"


@pytest.mark.freeze_time("2025-01-01 00:30:00+01:00")
async def test_graphql_electricity_no_prices(
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
            text=load_fixtures("graphql/energy_no_prices.json"),
        ),
    )
    today = date(2025, 5, 31)
    energy: EnergyPrices = await energyzero_client.get_electricity_prices(
        start_date=today,
        end_date=today,
        price_type=PriceType.ALL_IN,
    )
    assert energy == snapshot
    assert energy.extreme_prices is None
    assert energy.highest_price_time_range is None
    assert energy.lowest_price_time_range is None
    assert energy.pct_of_max_price is None
    assert energy.time_ranges_priced_equal_or_lower is None


async def test_empty_energyprices() -> None:
    """Verify that an empty EnergyPrices returns None where applicable."""
    prices = EnergyPrices(dict[TimeRange, float](), 0)
    assert prices.current_price is None
    assert prices.extreme_prices is None
    assert prices.highest_price_time_range is None
    assert prices.lowest_price_time_range is None
    assert prices.pct_of_max_price is None

    assert len(prices.timestamp_prices) == 0
    assert prices.time_ranges_priced_equal_or_lower is None
    assert isinstance(prices.utcnow(), datetime)
    assert prices.price_at_time(datetime.now(UTC)) is None


@pytest.mark.freeze_time("2025-05-31 15:00:00+01:00")
async def test_energyprices_fromdict() -> None:
    """Verify that an empty EnergyPrices returns None where applicable."""
    data = loads(load_fixtures("graphql/energy.json"))["data"]
    prices = EnergyPrices.from_dict(data, PriceType.ALL_IN)

    today = date(2025, 5, 31)

    assert prices.current_price == 0.1566829
    assert prices.extreme_prices == (0.1408077, 0.3895111)
    assert prices.lowest_price_time_range == TimeRange(
        datetime.combine(today, time(11, 0, 0), UTC),
        datetime.combine(today, time(12, 0, 0), UTC),
    )
    assert prices.highest_price_time_range == TimeRange(
        datetime.combine(today, time(19, 0, 0), UTC),
        datetime.combine(today, time(20, 0, 0), UTC),
    )

    assert prices.pct_of_max_price == 40.23

    assert len(prices.timestamp_prices) == 24
    assert prices.time_ranges_priced_equal_or_lower == 6
