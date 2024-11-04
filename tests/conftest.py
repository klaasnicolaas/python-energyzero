"""Fixture for the energyzero tests."""

from collections.abc import AsyncGenerator

import pytest
from aiohttp import ClientSession

from energyzero import EnergyZero


@pytest.fixture(name="energyzero_client")
async def client() -> AsyncGenerator[EnergyZero, None]:
    """Return an EnergyZero client."""
    async with (
        ClientSession() as session,
        EnergyZero(session=session) as energyzero_client,
    ):
        yield energyzero_client
