"""Regression coverage for gas blocks spanning local calendar days."""

import json
from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from energyzero import EnergyPrices, EnergyZero, Interval, PriceType
from energyzero.models import REST_PRICE_STREAMS

from . import load_fixtures


@pytest.mark.parametrize("price_type", list(PriceType))
@pytest.mark.parametrize(
    ("timezone", "midnight_block", "block_count"),
    [
        ("Europe/Amsterdam", 0, 2),
        ("UTC", 0, 2),
        ("America/New_York", 1, 1),
        ("Asia/Tokyo", 0, 2),
    ],
)
async def test_gas_calendar_day_overlap(
    energyzero_client: EnergyZero,
    price_type: PriceType,
    timezone: str,
    midnight_block: int,
    block_count: int,
) -> None:
    """Keep yesterday's still-valid gas block, including after a fresh start."""
    payload = json.loads(load_fixtures("rest/gas_day_response.json"))
    tz = ZoneInfo(timezone)
    with patch.object(energyzero_client._client, "_request", return_value=payload):
        prices = await energyzero_client.get_gas_prices(
            date(2025, 12, 17), price_type=price_type, local_tz=tz
        )

    stream = payload[REST_PRICE_STREAMS[price_type]]
    midnight = datetime(2025, 12, 17, tzinfo=tz).astimezone(UTC)
    expected = float(stream[midnight_block]["price"]["value"])
    assert len(prices.prices) == block_count
    assert prices.price_at_time(midnight) == expected
    with patch.object(EnergyPrices, "utcnow", return_value=midnight):
        assert prices.current_price == expected
    assert prices.price_at_time(datetime(2025, 12, 17, 5, tzinfo=UTC)) == float(
        stream[1]["price"]["value"]
    )
    assert prices.price_at_time(datetime(2025, 12, 18, 5, tzinfo=UTC)) is None


@pytest.mark.parametrize(
    ("day", "hours"),
    [
        pytest.param(date(2026, 1, 15), 24, id="winter"),
        pytest.param(date(2026, 4, 10), 24, id="summer"),
        pytest.param(date(2026, 3, 29), 23, id="spring-transition"),
        pytest.param(date(2025, 10, 26), 25, id="autumn-transition"),
    ],
)
async def test_gas_day_boundaries(
    energyzero_client: EnergyZero, day: date, hours: int
) -> None:
    """Use the API's UTC validity ranges across both clock changes."""
    tz = ZoneInfo("Europe/Amsterdam")
    boundary = datetime.combine(day, datetime.min.time(), tz).replace(hour=6)
    start = (boundary - timedelta(days=1)).astimezone(UTC)
    end = boundary.astimezone(UTC)
    next_end = (boundary + timedelta(days=1)).astimezone(UTC)
    blocks = [
        {
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
            "price": {"value": "0"},
        },
        {
            "start": end.isoformat().replace("+00:00", "Z"),
            "end": next_end.isoformat().replace("+00:00", "Z"),
            "price": {"value": "0.5"},
        },
    ]
    payload = dict.fromkeys(REST_PRICE_STREAMS.values(), blocks)
    with patch.object(energyzero_client._client, "_request", return_value=payload):
        prices = await energyzero_client.get_gas_prices(day, local_tz=tz)

    assert end - start == timedelta(hours=hours)
    assert len(prices.prices) == 2
    assert prices.price_at_time(start) == 0
    assert prices.price_at_time(end - timedelta(microseconds=1)) == 0
    assert prices.price_at_time(end) == 0.5
    assert prices.price_at_time(next_end) is None
    with patch.object(EnergyPrices, "utcnow", return_value=end - timedelta(minutes=30)):
        assert prices.current_price == 0
        assert prices.price_at_time(prices.utcnow() + timedelta(hours=1)) == 0.5


async def test_gas_does_not_extend_expired_block(energyzero_client: EnergyZero) -> None:
    """Missing new prices must not reuse an expired gas price."""
    payload = json.loads(load_fixtures("rest/gas_day_response.json"))
    for stream in REST_PRICE_STREAMS.values():
        payload[stream] = payload[stream][:1]
    with patch.object(energyzero_client._client, "_request", return_value=payload):
        prices = await energyzero_client.get_gas_prices(
            date(2025, 12, 17), local_tz=ZoneInfo("Europe/Amsterdam")
        )
    with patch.object(
        EnergyPrices, "utcnow", return_value=datetime(2025, 12, 17, 5, tzinfo=UTC)
    ):
        assert prices.current_price is None


@pytest.mark.parametrize(
    ("day", "hours"), [(date(2026, 3, 29), 23), (date(2025, 10, 26), 25)]
)
@pytest.mark.parametrize("minutes", [15, 60])
async def test_electricity_calendar_day_across_dst(
    energyzero_client: EnergyZero, day: date, hours: int, minutes: int
) -> None:
    """Overlap filtering keeps precisely the electricity periods in a local day."""
    tz = ZoneInfo("Europe/Amsterdam")
    start = datetime.combine(day, datetime.min.time(), tz).astimezone(UTC)
    end = datetime.combine(day + timedelta(days=1), datetime.min.time(), tz).astimezone(
        UTC
    )
    step = timedelta(minutes=minutes)
    count = hours * 60 // minutes
    blocks = [
        {
            "start": (start + index * step).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": (start + (index + 1) * step).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "price": {"value": "0.2"},
        }
        for index in range(-1, count + 1)
    ]
    with patch.object(
        energyzero_client._client,
        "_request",
        return_value=dict.fromkeys(REST_PRICE_STREAMS.values(), blocks),
    ):
        prices = await energyzero_client.get_electricity_prices(
            day,
            interval=Interval.HOUR if minutes == 60 else Interval.QUARTER,
            local_tz=tz,
        )

    assert len(prices.prices) == count
    assert prices.price_at_time(start - step) is None
    assert prices.price_at_time(start) == 0.2
    assert prices.price_at_time(end - step) == 0.2
    assert prices.price_at_time(end) is None
    assert prices.average_price == pytest.approx(0.2)
