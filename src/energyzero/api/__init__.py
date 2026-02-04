"""API clients for EnergyZero."""

from __future__ import annotations

import enum

from .base import EnergyZeroAPIProtocol


class APIBackend(enum.StrEnum):
    """Available API backends."""

    REST = "rest"
    GRAPHQL = "graphql"


__all__ = ["APIBackend", "EnergyZeroAPIProtocol"]
