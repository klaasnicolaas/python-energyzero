"""Tests for EnergyPriceBlock class."""

from datetime import UTC, datetime

import pytest

from energyzero import (
    EnergyPriceBlock,
    TimeRange,
)


def test_energy_price_block_with_costs() -> None:
    """Test EnergyPriceBlock with additional costs."""
    time_range = TimeRange(
        datetime(2025, 6, 23, 12, 0, tzinfo=UTC),
        datetime(2025, 6, 23, 13, 0, tzinfo=UTC),
    )
    block = EnergyPriceBlock(
        time_range=time_range,
        energy_price_excl=0.30,
        energy_price_incl=0.36,
        vat=0.06,
        additional_costs=[
            {"priceExcl": 0.05, "priceIncl": 0.06},
            {"priceExcl": 0.02, "priceIncl": 0.03},
        ],
    )
    assert block.total_excl == pytest.approx(0.37)
    assert block.total_incl == pytest.approx(0.45)


def test_energy_price_block_without_costs() -> None:
    """Test EnergyPriceBlock without additional costs."""
    time_range = TimeRange(
        datetime(2025, 6, 23, 12, 0, tzinfo=UTC),
        datetime(2025, 6, 23, 13, 0, tzinfo=UTC),
    )
    block = EnergyPriceBlock(
        time_range=time_range,
        energy_price_excl=0.40,
        energy_price_incl=0.48,
        vat=0.08,
        additional_costs=[],
    )
    assert block.total_excl == 0.40
    assert block.total_incl == 0.48
