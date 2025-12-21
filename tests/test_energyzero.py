"""Basic tests for the EnergyZero API clients."""

# pylint: disable=protected-access
import asyncio
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, cast
from unittest.mock import patch

import pytest
from aiohttp import ClientError, ClientResponse, ClientSession
from aresponses import Response, ResponsesMockServer

from energyzero import EnergyZero
from energyzero.api.graphql import GraphQLClient
from energyzero.api.rest import RESTClient
from energyzero.exceptions import EnergyZeroConnectionError, EnergyZeroError

from . import load_fixtures

if TYPE_CHECKING:
    from energyzero import APIBackend


@pytest.fixture(name="rest_client")
async def rest_client_fixture() -> AsyncIterator[RESTClient]:
    """Provide a REST client with a managed session."""
    async with ClientSession() as session:
        client = RESTClient(session=session)
        yield client
        await client.close()


@pytest.fixture(name="graphql_client")
async def graphql_client_fixture() -> AsyncIterator[GraphQLClient]:
    """Provide a GraphQL client with a managed session."""
    async with ClientSession() as session:
        client = GraphQLClient(session=session)
        yield client
        await client.close()


async def test_rest_json_request(
    aresponses: ResponsesMockServer, rest_client: RESTClient
) -> None:
    """Test REST client handles JSON response."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"ok": true}',
        ),
    )
    await rest_client._request("public/v1/test")


async def test_graphql_json_request(
    aresponses: ResponsesMockServer, graphql_client: GraphQLClient
) -> None:
    """Test GraphQL client handles JSON response."""
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
    await graphql_client._request("gql", json={"query": "{}"})


async def test_rest_internal_session(aresponses: ResponsesMockServer) -> None:
    """Ensure REST client creates an internal session when needed."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"ok": true}',
        ),
    )
    client = RESTClient()
    await client._request("public/v1/test")
    await client.close()


async def test_graphql_internal_session(aresponses: ResponsesMockServer) -> None:
    """Ensure GraphQL client creates an internal session when needed."""
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
    client = GraphQLClient()
    await client._request("gql", json={"query": "{}"})
    await client.close()


async def test_rest_timeout(aresponses: ResponsesMockServer) -> None:
    """Test REST client timeout handling."""

    async def response_handler(_: ClientResponse) -> Response:
        await asyncio.sleep(0.2)
        return aresponses.Response(body="Goodmorning!")

    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/test",
        "GET",
        response_handler,
    )

    async with ClientSession() as session:
        client = RESTClient(session=session, request_timeout=0.1)
        with pytest.raises(EnergyZeroConnectionError):
            await client._request("public/v1/test")


async def test_graphql_timeout(aresponses: ResponsesMockServer) -> None:
    """Test GraphQL client timeout handling."""

    async def response_handler(_: ClientResponse) -> Response:
        await asyncio.sleep(0.2)
        return aresponses.Response(body="Goodmorning!")

    aresponses.add("api.energyzero.nl", "/v1/gql", "POST", response_handler)

    async with ClientSession() as session:
        client = GraphQLClient(session=session, request_timeout=0.1)
        with pytest.raises(EnergyZeroConnectionError):
            await client._request("gql", json={"query": "{}"})


async def test_rest_content_type(
    aresponses: ResponsesMockServer, rest_client: RESTClient
) -> None:
    """Test REST client raises on invalid content type."""
    aresponses.add(
        "public.api.energyzero.nl",
        "/public/v1/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "blabla/blabla"},
        ),
    )
    with pytest.raises(EnergyZeroError):
        await rest_client._request("public/v1/test")


async def test_graphql_content_type(
    aresponses: ResponsesMockServer, graphql_client: GraphQLClient
) -> None:
    """Test GraphQL client raises on invalid content type."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "blabla/blabla"},
        ),
    )
    with pytest.raises(EnergyZeroError):
        await graphql_client._request("gql", json={"query": "{}"})


async def test_rest_client_error() -> None:
    """Test REST client handles aiohttp ClientError."""
    async with ClientSession() as session:
        client = RESTClient(session=session)
        with (
            patch.object(session, "request", side_effect=ClientError),
            pytest.raises(EnergyZeroConnectionError),
        ):
            await client._request("public/v1/test")


async def test_graphql_client_error() -> None:
    """Test GraphQL client handles aiohttp ClientError."""
    async with ClientSession() as session:
        client = GraphQLClient(session=session)
        with (
            patch.object(session, "request", side_effect=ClientError),
            pytest.raises(EnergyZeroConnectionError),
        ):
            await client._request("gql", json={"query": "{}"})


async def test_graphql_server_error(
    aresponses: ResponsesMockServer, graphql_client: GraphQLClient
) -> None:
    """Test GraphQL client raises on API error payload."""
    aresponses.add(
        "api.energyzero.nl",
        "/v1/gql",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("graphql/gql_error.json"),
        ),
    )
    with pytest.raises(EnergyZeroError):
        await graphql_client._request("gql", json={"query": "{}"})


async def test_energyzero_sets_close_flag_when_no_session() -> None:
    """EnergyZero should mark that it owns the session when none provided."""
    client = EnergyZero()
    assert client._close_session is True
    await client.close()


def test_energyzero_invalid_backend() -> None:
    """EnergyZero should reject unknown backends."""
    invalid_backend = cast("APIBackend", "invalid")
    with pytest.raises(ValueError, match="Unknown backend"):
        EnergyZero(backend=invalid_backend)
