"""API clients for EnergyZero."""

from __future__ import annotations

from enum import StrEnum

from .base import EnergyZeroAPIProtocol


class APIBackend(StrEnum):
    """Available API backends."""

    REST = "rest"
    GRAPHQL = "graphql"


__all__ = ["APIBackend", "EnergyZeroAPIProtocol"]
