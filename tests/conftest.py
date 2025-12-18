"""Fixture for the energyzero tests."""

from collections.abc import AsyncIterator

import pytest
from aiohttp import ClientSession

from energyzero import APIBackend, EnergyZero


@pytest.fixture(name="energyzero_client")
async def client() -> AsyncIterator[EnergyZero]:
    """Return an EnergyZero client using the REST backend."""
    async with (
        ClientSession() as session,
        EnergyZero(session=session, backend=APIBackend.REST) as energyzero_client,
    ):
        yield energyzero_client


@pytest.fixture(name="graphql_energyzero_client")
async def graphql_client() -> AsyncIterator[EnergyZero]:
    """Return an EnergyZero client using the GraphQL backend."""
    async with (
        ClientSession() as session,
        EnergyZero(session=session, backend=APIBackend.GRAPHQL) as energyzero_client,
    ):
        yield energyzero_client
