"""Test retrieving multiple price types with one backend request."""

import json
from datetime import UTC, date, datetime, timedelta
from typing import assert_type
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from aresponses import ResponsesMockServer

from energyzero import APIBackend, EnergyPrices, EnergyZero, Interval, PriceType
from energyzero.exceptions import EnergyZeroNoDataError

from . import load_fixtures


@pytest.mark.parametrize(
    ("kind", "interval", "fixture"),
    [
        ("electricity", Interval.HOUR, "electricity_hour_response"),
        ("electricity", Interval.QUARTER, "electricity_quarter_response"),
        ("gas", Interval.DAY, "gas_day_response"),
    ],
)
async def test_rest_multiple_types(
    aresponses: ResponsesMockServer,
    energyzero_client: EnergyZero,
    kind: str,
    interval: Interval,
    fixture: str,
) -> None:
    """Fetch all streams once, filtering every stream to the local day."""
    payload = json.loads(load_fixtures(f"rest/{fixture}.json"))
    aresponses.add(
        "public.api.energyzero.nl",
        f"/public/v1/prices?energyType=ENERGY_TYPE_{kind.upper()}"
        f"&date=17-12-2025&interval={interval.value}",
        "GET",
        aresponses.Response(
            text=json.dumps(payload), headers={"Content-Type": "application/json"}
        ),
        match_querystring=True,
    )
    local_tz = ZoneInfo("Europe/Amsterdam")
    requested_date = date(2025, 12, 17)
    method = getattr(energyzero_client, f"get_{kind}_prices")
    result = await method(
        requested_date,
        price_type=iter([*PriceType, PriceType.ALL_IN]),
        local_tz=local_tz,
        **({"interval": interval} if kind == "electricity" else {}),
    )
    assert list(result) == list(PriceType)
    count = {Interval.HOUR: 24, Interval.QUARTER: 96, Interval.DAY: 1}[interval]
    for price_type, stream in (
        (PriceType.MARKET, "base"),
        (PriceType.MARKET_WITH_VAT, "base_with_vat"),
        (PriceType.ALL_IN_EXCL_VAT, "all_in"),
        (PriceType.ALL_IN, "all_in_with_vat"),
    ):
        expected = [
            float(item["price"]["value"])
            for item in payload[stream]
            if datetime.fromisoformat(item["start"]).astimezone(local_tz).date()
            == requested_date
        ]
        prices = result[price_type]
        assert len(prices.prices) == count
        assert list(prices.prices.values()) == expected
        assert prices.average_price == pytest.approx(sum(expected) / count)
        assert all(
            time_range.start_including.astimezone(local_tz).date() == requested_date
            for time_range in prices.prices
        )
    assert len(aresponses.history) == 1
    aresponses.assert_plan_strictly_followed()


@pytest.mark.parametrize("backend", list(APIBackend))
@pytest.mark.parametrize("kind", ["electricity", "gas"])
async def test_empty_types(backend: APIBackend, kind: str) -> None:
    """Reject an empty iterable without contacting the backend."""
    async with EnergyZero(backend=backend) as client:
        with (
            patch.object(client._client, "_request") as request,
            pytest.raises(ValueError, match="At least one price type"),
        ):
            await getattr(client, f"get_{kind}_prices")(
                date(2025, 12, 17), price_type=iter(())
            )
        request.assert_not_called()


@pytest.mark.parametrize("kind", ["electricity", "gas"])
@pytest.mark.parametrize("backend", list(APIBackend))
async def test_invalid_dates(backend: APIBackend, kind: str) -> None:
    """Keep backend date validation and reject invalid dates before requesting."""
    async with EnergyZero(backend=backend) as client:
        with (
            patch.object(client._client, "_request") as request,
            pytest.raises(ValueError, match=r"single-day|end_date is required"),
        ):
            await getattr(client, f"get_{kind}_prices")(
                date(2025, 12, 17),
                date(2025, 12, 18) if backend == APIBackend.REST else None,
                price_type=(PriceType.MARKET_WITH_VAT, PriceType.ALL_IN),
            )
        request.assert_not_called()


@pytest.mark.parametrize("kind", ["electricity", "gas"])
@pytest.mark.parametrize("stream_state", ["empty", "other_day", "absent"])
async def test_missing_requested_day(
    energyzero_client: EnergyZero, kind: str, stream_state: str
) -> None:
    """Fail the whole call if one requested stream has no prices for the day."""
    fixture = (
        "electricity_hour_response" if kind == "electricity" else "gas_day_response"
    )
    payload = json.loads(load_fixtures(f"rest/{fixture}.json"))
    payload["all_in_with_vat"] = (
        [] if stream_state == "empty" else [payload["all_in_with_vat"][0]]
    )
    if stream_state == "absent":
        del payload["all_in_with_vat"]
    with (
        patch.object(
            energyzero_client._client, "_request", return_value=payload
        ) as request,
        pytest.raises(EnergyZeroNoDataError, match="2025-12-17"),
    ):
        await getattr(energyzero_client, f"get_{kind}_prices")(
            date(2025, 12, 17),
            price_type=(PriceType.MARKET_WITH_VAT, PriceType.ALL_IN),
            local_tz=ZoneInfo("Europe/Amsterdam"),
        )
    request.assert_awaited_once()


@pytest.mark.parametrize("kind", ["electricity", "gas"])
async def test_graphql_multiple_types(
    aresponses: ResponsesMockServer,
    graphql_energyzero_client: EnergyZero,
    kind: str,
) -> None:
    """Build all GraphQL price flavors from one response."""
    fixture = "energy" if kind == "electricity" else "gas"
    payload = json.loads(load_fixtures(f"graphql/{fixture}.json"))
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            text=json.dumps(payload), headers={"Content-Type": "application/json"}
        ),
    )
    result = await getattr(graphql_energyzero_client, f"get_{kind}_prices")(
        date(2025, 5, 31), date(2025, 6, 1), price_type=iter(PriceType)
    )
    assert list(result) == list(PriceType)
    items = payload["data"]["energyMarketPrices"]["prices"]
    for price_type, field, cost_field in (
        (PriceType.MARKET, "energyPriceExcl", None),
        (PriceType.MARKET_WITH_VAT, "energyPriceIncl", None),
        (PriceType.ALL_IN_EXCL_VAT, "energyPriceExcl", "priceExcl"),
        (PriceType.ALL_IN, "energyPriceIncl", "priceIncl"),
    ):
        expected = [
            item[field]
            + (
                sum(cost[cost_field] for cost in item["additionalCosts"])
                if cost_field
                else 0
            )
            for item in items
        ]
        assert list(result[price_type].prices.values()) == expected
        assert result[price_type].average_price == pytest.approx(
            sum(expected) / len(expected)
        )
    assert len(aresponses.history) == 1
    aresponses.assert_plan_strictly_followed()


@pytest.mark.parametrize(
    ("day", "hours"), [(date(2025, 3, 30), 23), (date(2025, 10, 26), 25)]
)
async def test_multiple_types_dst(
    energyzero_client: EnergyZero, day: date, hours: int
) -> None:
    """Keep the full local day across both daylight saving transitions."""
    local_tz = ZoneInfo("Europe/Amsterdam")
    midnight = datetime.combine(day, datetime.min.time(), local_tz).astimezone(UTC)
    payload = {
        stream: [
            {
                "start": (midnight + timedelta(hours=hour)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "end": (midnight + timedelta(hours=hour + 1)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "price": {"value": str(value)},
            }
            for hour in range(-2, hours + 2)
        ]
        for value, stream in enumerate(
            ("base", "base_with_vat", "all_in", "all_in_with_vat")
        )
    }
    with patch.object(
        energyzero_client._client, "_request", return_value=payload
    ) as request:
        result = await energyzero_client.get_electricity_prices(
            day, interval=Interval.HOUR, price_type=PriceType, local_tz=local_tz
        )
    request.assert_awaited_once()
    for prices in result.values():
        assert len(prices.prices) == hours
        assert all(
            timerange.start_including.astimezone(local_tz).date() == day
            for timerange in prices.prices
        )


@pytest.mark.parametrize("backend", list(APIBackend))
@pytest.mark.parametrize("kind", ["electricity", "gas"])
async def test_subset_and_single_price_compatibility(
    backend: APIBackend, kind: str
) -> None:
    """Preserve single-price defaults and return only the requested types."""
    if backend == APIBackend.REST:
        fixture = (
            "electricity_hour_response" if kind == "electricity" else "gas_day_response"
        )
    else:
        fixture = "energy" if kind == "electricity" else "gas"
    payload = json.loads(load_fixtures(f"{backend.value}/{fixture}.json"))
    async with EnergyZero(backend=backend) as client:
        with patch.object(client._client, "_request", return_value=payload) as request:
            method = getattr(client, f"get_{kind}_prices")
            result = await method(
                date(2025, 12, 17),
                date(2025, 12, 17),
                price_type=iter(
                    (PriceType.ALL_IN, PriceType.MARKET_WITH_VAT, PriceType.ALL_IN)
                ),
                local_tz=ZoneInfo("Europe/Amsterdam"),
            )
            request.assert_awaited_once()
            assert list(result) == [PriceType.ALL_IN, PriceType.MARKET_WITH_VAT]
            single = await getattr(client, f"get_{kind}_prices")(
                date(2025, 12, 17),
                date(2025, 12, 17),
                local_tz=ZoneInfo("Europe/Amsterdam"),
            )
            assert single == result[PriceType.ALL_IN]


@pytest.mark.parametrize("backend", list(APIBackend))
@pytest.mark.parametrize("kind", ["electricity", "gas"])
@pytest.mark.parametrize("container", [tuple, list, set, iter])
async def test_singleton_iterable(
    backend: APIBackend, kind: str, container: type
) -> None:
    """An iterable with one type returns a mapping, including positional calls."""
    if backend == APIBackend.REST:
        fixture = (
            "electricity_hour_response" if kind == "electricity" else "gas_day_response"
        )
    else:
        fixture = "energy" if kind == "electricity" else "gas"
    payload = json.loads(load_fixtures(f"{backend.value}/{fixture}.json"))
    day = date(2025, 12, 17)
    async with EnergyZero(backend=backend) as client:
        with patch.object(client._client, "_request", return_value=payload) as request:
            selected = container([PriceType.MARKET_WITH_VAT])
            if kind == "electricity":
                result = await client.get_electricity_prices(
                    day, day, Interval.HOUR, selected
                )
            else:
                result = await client.get_gas_prices(day, day, selected)
            request.assert_awaited_once()
            assert isinstance(result, dict)
            assert list(result) == [PriceType.MARKET_WITH_VAT]
            assert isinstance(result[PriceType.MARKET_WITH_VAT], EnergyPrices)


@pytest.mark.parametrize("backend", list(APIBackend))
async def test_return_type_overloads(backend: APIBackend) -> None:
    """Check type inference alongside actual return values for both methods."""
    payload = json.loads(
        load_fixtures(
            "rest/electricity_hour_response.json"
            if backend == APIBackend.REST
            else "graphql/energy.json"
        )
    )
    day = date(2025, 12, 17)
    async with EnergyZero(backend=backend) as client:
        with patch.object(client._client, "_request", return_value=payload):
            electricity = assert_type(
                await client.get_electricity_prices(day, day), EnergyPrices
            )
            gas = assert_type(await client.get_gas_prices(day, day), EnergyPrices)
            assert isinstance(electricity, EnergyPrices)
            assert isinstance(gas, EnergyPrices)
            assert_type(
                await client.get_electricity_prices(
                    day, day, Interval.HOUR, PriceType.ALL_IN
                ),
                EnergyPrices,
            )
            assert_type(
                await client.get_gas_prices(day, day, PriceType.ALL_IN), EnergyPrices
            )
            electricity_types = assert_type(
                await client.get_electricity_prices(
                    day, day, price_type=(PriceType.ALL_IN,)
                ),
                dict[PriceType, EnergyPrices],
            )
            gas_types = assert_type(
                await client.get_gas_prices(day, day, price_type=(PriceType.ALL_IN,)),
                dict[PriceType, EnergyPrices],
            )
            assert electricity_types == {PriceType.ALL_IN: electricity}
            assert gas_types == {PriceType.ALL_IN: gas}
            assert_type(
                await client.get_electricity_prices(
                    day, day, Interval.HOUR, iter(PriceType)
                ),
                dict[PriceType, EnergyPrices],
            )
            assert_type(
                await client.get_gas_prices(day, day, [PriceType.ALL_IN]),
                dict[PriceType, EnergyPrices],
            )
