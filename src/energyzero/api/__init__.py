"""API clients for EnergyZero."""

from __future__ import annotations

from enum import Enum

from .base import EnergyZeroAPIProtocol


class APIBackend(str, Enum):
    """Available API backends."""

    REST = "rest"
    GRAPHQL = "graphql"


__all__ = ["APIBackend", "EnergyZeroAPIProtocol"]
