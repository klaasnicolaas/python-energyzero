"""Tests for EnergyZero exceptions."""

from energyzero.exceptions import EnergyZeroConnectionError, EnergyZeroNoDataError


def test_connection_error_prefers_explicit_message() -> None:
    """Ensure explicit messages are preserved."""
    err = EnergyZeroConnectionError(message="Boom")
    assert str(err) == "Boom"
    assert err.data is None
    assert err.status is None


def test_connection_error_uses_payload_message() -> None:
    """Ensure API payload message is surfaced."""
    payload = {"message": "payload failure"}
    err = EnergyZeroConnectionError(data=payload, status=404)
    assert str(err) == "payload failure"
    assert err.data == payload
    assert err.status == 404


def test_connection_error_status_fallback() -> None:
    """Ensure HTTP status fallback is used."""
    err = EnergyZeroConnectionError(status=500)
    assert str(err) == "Error occurred while communicating with the API. (HTTP 500)"


def test_connection_error_empty_payload_message_uses_status() -> None:
    """Ensure empty payload messages fall back to HTTP status."""
    payload = {"message": ""}
    err = EnergyZeroConnectionError(data=payload, status=502)
    assert str(err) == "Error occurred while communicating with the API. (HTTP 502)"


def test_no_data_error_default_message() -> None:
    """Ensure EnergyZeroNoDataError has a helpful default."""
    err = EnergyZeroNoDataError()
    assert str(err) == "No data available for the requested period."
