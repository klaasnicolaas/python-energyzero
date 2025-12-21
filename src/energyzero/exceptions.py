"""Exceptions for EnergyZero."""

from __future__ import annotations

from typing import Any, cast


def _build_message(
    message: str | None,
    *,
    data: dict[str, Any] | None,
    status: int | None,
    default: str,
) -> str:
    """Return a human readable message."""
    if message is not None:
        return message

    if data and isinstance(data.get("message"), str):
        data_message = cast("str", data["message"])
        if data_message:
            return data_message

    if status is not None:
        return f"{default} (HTTP {status})"

    return default


class EnergyZeroError(Exception):
    """Generic EnergyZero exception."""


class EnergyZeroConnectionError(EnergyZeroError):
    """EnergyZero - connection exception."""

    def __init__(
        self,
        message: str | None = None,
        *,
        data: dict[str, Any] | None = None,
        status: int | None = None,
        default: str = "Error occurred while communicating with the API.",
    ) -> None:
        """Initialize the connection error."""
        super().__init__(
            _build_message(message, data=data, status=status, default=default),
        )
        self.data = data
        self.status = status


class EnergyZeroNoDataError(EnergyZeroError):
    """EnergyZero - no data exception."""

    def __init__(
        self,
        message: str | None = None,
        *,
        data: dict[str, Any] | None = None,
        status: int | None = None,
        default: str = "No data available for the requested period.",
    ) -> None:
        """Initialize the no-data error."""
        super().__init__(
            _build_message(message, data=data, status=status, default=default),
        )
        self.data = data
        self.status = status
