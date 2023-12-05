"""Constants for EnergyZero API client."""
from __future__ import annotations

from enum import Enum


class VatCategory(str, Enum):
    """Enumeration representing the VAT category."""

    INCL = "true"
    EXCL = "false"
