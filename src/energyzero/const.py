"""Constants for EnergyZero API client."""

from __future__ import annotations

from enum import Enum


class VatOption(str, Enum):
    """Enum representing whether to include VAT or not."""

    INCLUDE = "true"
    EXCLUDE = "false"
