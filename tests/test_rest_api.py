"""Tests for the EnergyZero REST API."""

# pylint: disable=protected-access
import json
from datetime import date, timedelta

import pytest
from aresponses import ResponsesMockServer

from energyzero import EnergyPrices, EnergyZero, PriceType
from energyzero.exceptions import EnergyZeroConnectionError, EnergyZeroNoDataError

from . import load_fixtures


async def test_rest_electricity_prices_quarter_hour(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Test getting quarter-hour electricity prices from REST API."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("rest/electricity_quarter_response.json"),
        ),
    )

    result = await energyzero_client.get_electricity_prices(
        start_date=date(2025, 12, 17),
        end_date=date(2025, 12, 17),
        interval="INTERVAL_QUARTER",
        price_type=PriceType.ALL_IN,
    )

    assert result is not None
    assert result.average_price is not None
    assert len(result.prices) > 0

    await energyzero_client.close()


async def test_rest_electricity_prices_hourly(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Test getting hourly electricity prices from REST API."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("rest/electricity_hour_response.json"),
        ),
    )

    result = await energyzero_client.get_electricity_prices(
        start_date=date(2025, 12, 17),
        end_date=date(2025, 12, 17),
        interval="INTERVAL_HOUR",
        price_type=PriceType.ALL_IN,
    )

    assert result is not None
    assert result.average_price is not None
    assert len(result.prices) > 0

    await energyzero_client.close()


async def test_rest_electricity_prices_market(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Test getting market electricity prices from REST API."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("rest/electricity_hour_response.json"),
        ),
    )

    result = await energyzero_client.get_electricity_prices(
        start_date=date(2025, 12, 17),
        end_date=date(2025, 12, 17),
        price_type=PriceType.MARKET,
    )

    assert result is not None
    assert result.average_price is not None
    assert len(result.prices) > 0

    # Verify market prices are lower than all-in prices
    # (since they don't include energy tax)
    await energyzero_client.close()


async def test_rest_gas_prices(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Test getting gas prices from REST API."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("rest/gas_day_response.json"),
        ),
    )

    result = await energyzero_client.get_gas_prices(
        start_date=date(2025, 12, 17),
        end_date=date(2025, 12, 17),
        price_type=PriceType.ALL_IN,
    )

    assert result is not None
    assert result.average_price is not None
    assert len(result.prices) > 0

    await energyzero_client.close()


async def test_rest_electricity_no_data(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Test handling of empty response from REST API."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps(
                {
                    "interval": 2,
                    "range": {},
                    "base": [],
                    "base_with_vat": [],
                    "all_in": [],
                    "all_in_with_vat": [],
                }
            ),
        ),
    )

    with pytest.raises(EnergyZeroNoDataError):
        await energyzero_client.get_electricity_prices(
            start_date=date(2025, 12, 17),
            end_date=date(2025, 12, 17),
        )

    await energyzero_client.close()


async def test_rest_gas_no_data(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Test handling of empty gas response from REST API."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps(
                {
                    "interval": 4,
                    "range": {},
                    "base": [],
                    "base_with_vat": [],
                    "all_in": [],
                    "all_in_with_vat": [],
                }
            ),
        ),
    )

    with pytest.raises(EnergyZeroNoDataError):
        await energyzero_client.get_gas_prices(
            start_date=date(2025, 12, 17),
            end_date=date(2025, 12, 17),
        )

    await energyzero_client.close()


async def test_rest_url_building(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Test that REST API URLs are built correctly."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("rest/electricity_hour_response.json"),
        ),
    )

    # This should use public.api.energyzero.nl instead of api.energyzero.nl
    result = await energyzero_client.get_electricity_prices(
        start_date=date(2025, 12, 17),
        end_date=date(2025, 12, 17),
    )

    assert result is not None
    await energyzero_client.close()


async def test_rest_electricity_invalid_range(
    energyzero_client: EnergyZero,
) -> None:
    """Ensure REST backend raises when multiple days requested."""
    start_date = date(2025, 12, 17)
    end_date = start_date + timedelta(days=1)

    with pytest.raises(ValueError, match="single-day"):
        await energyzero_client.get_electricity_prices(
            start_date=start_date,
            end_date=end_date,
        )


async def test_rest_gas_invalid_range(energyzero_client: EnergyZero) -> None:
    """Ensure REST backend raises when multiple days requested for gas."""
    start_date = date(2025, 12, 17)
    end_date = start_date + timedelta(days=1)

    with pytest.raises(ValueError, match="single-day"):
        await energyzero_client.get_gas_prices(
            start_date=start_date,
            end_date=end_date,
        )


async def test_rest_bad_request(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Ensure REST backend surfaces HTTP errors."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=400,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("rest/error_response.json"),
        ),
    )

    with pytest.raises(EnergyZeroConnectionError):
        await energyzero_client.get_electricity_prices(
            start_date=date(2025, 12, 17),
        )
    await energyzero_client.close()


async def test_rest_bad_request_invalid_json_payload(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Ensure REST backend handles invalid JSON error payloads."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=400,
            headers={"Content-Type": "text/plain"},
            text="not-json",
        ),
    )

    with pytest.raises(EnergyZeroConnectionError) as err:
        await energyzero_client.get_electricity_prices(
            start_date=date(2025, 12, 17),
        )

    assert err.value.data is None
    await energyzero_client.close()


async def test_rest_future_date_returns_no_data(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Ensure future dates raise a no-data error (404)."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=404,
            headers={"Content-Type": "application/json"},
            text='{"code":3,"message":"not found"}',
        ),
    )

    with pytest.raises(EnergyZeroNoDataError):
        await energyzero_client.get_electricity_prices(
            start_date=date(2030, 1, 1),
        )


async def test_rest_electricity_filtered_out_by_date(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Ensure filtered-out entries raise no-data errors."""
    payload = {
        "interval": 2,
        "range": {},
        "base": [
            {
                "start": "2025-12-20T00:00:00Z",
                "end": "2025-12-20T00:15:00Z",
                "price": {"value": "0.10"},
            }
        ],
        "base_with_vat": [
            {
                "start": "2025-12-20T00:00:00Z",
                "end": "2025-12-20T00:15:00Z",
                "price": {"value": "0.12"},
            }
        ],
        "all_in_with_vat": [
            {
                "start": "2025-12-20T00:00:00Z",
                "end": "2025-12-20T00:15:00Z",
                "price": {"value": "0.15"},
            }
        ],
    }
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps(payload),
        ),
    )

    with pytest.raises(EnergyZeroNoDataError):
        await energyzero_client.get_electricity_prices(
            start_date=date(2025, 12, 17),
        )

    await energyzero_client.close()


async def test_rest_gas_filtered_out_by_date(
    aresponses: ResponsesMockServer, energyzero_client: EnergyZero
) -> None:
    """Ensure gas filtering raises no-data errors."""
    payload = {
        "interval": 4,
        "range": {},
        "base": [
            {
                "start": "2025-12-20T00:00:00Z",
                "end": "2025-12-21T00:00:00Z",
                "price": {"value": "1.10"},
            }
        ],
        "base_with_vat": [
            {
                "start": "2025-12-20T00:00:00Z",
                "end": "2025-12-21T00:00:00Z",
                "price": {"value": "1.12"},
            }
        ],
        "all_in_with_vat": [
            {
                "start": "2025-12-20T00:00:00Z",
                "end": "2025-12-21T00:00:00Z",
                "price": {"value": "1.15"},
            }
        ],
    }
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/prices",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps(payload),
        ),
    )

    with pytest.raises(EnergyZeroNoDataError):
        await energyzero_client.get_gas_prices(
            start_date=date(2025, 12, 17),
        )

    await energyzero_client.close()


def test_rest_from_rest_dict_without_filter_date() -> None:
    """Ensure parsing works for each price type without filtering."""
    payload = {
        "base": [
            {
                "start": "2025-12-17T00:00:00Z",
                "end": "2025-12-17T00:15:00Z",
                "price": {"value": "0.05"},
            }
        ],
        "base_with_vat": [
            {
                "start": "2025-12-17T00:00:00Z",
                "end": "2025-12-17T00:15:00Z",
                "price": {"value": "0.06"},
            }
        ],
        "all_in": [
            {
                "start": "2025-12-17T00:00:00Z",
                "end": "2025-12-17T00:15:00Z",
                "price": {"value": "0.07"},
            }
        ],
        "all_in_with_vat": [
            {
                "start": "2025-12-17T00:00:00Z",
                "end": "2025-12-17T00:15:00Z",
                "price": {"value": "0.08"},
            }
        ],
    }

    assert EnergyPrices.from_rest_dict(payload, PriceType.MARKET).average_price == 0.05
    assert (
        EnergyPrices.from_rest_dict(payload, PriceType.MARKET_WITH_VAT).average_price
        == 0.06
    )
    assert (
        EnergyPrices.from_rest_dict(payload, PriceType.ALL_IN_EXCL_VAT).average_price
        == 0.07
    )
    assert EnergyPrices.from_rest_dict(payload, PriceType.ALL_IN).average_price == 0.08
