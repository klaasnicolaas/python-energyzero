"""Exceptions for EnergyZero."""


class EnergyZeroError(Exception):
    """Generic EnergyZero exception."""


class EnergyZeroConnectionError(EnergyZeroError):
    """EnergyZero - connection exception."""


class EnergyZeroNoDataError(EnergyZeroError):
    """EnergyZero - no data exception."""
