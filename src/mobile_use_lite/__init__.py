"""Mobile-Use Lite: self-hosted mobile GUI agent (P0 stub loop)."""

from __future__ import annotations

from .schema import E_COORD_RANGE, E_SCHEMA, SchemaError, validate_action, validate_turn
from .session import (
    CANCELLED,
    FAILED,
    RUNNING,
    SUCCEEDED,
    WAITING_HUMAN,
    Session,
)

__all__ = [
    "E_COORD_RANGE",
    "E_SCHEMA",
    "SchemaError",
    "validate_action",
    "validate_turn",
    "Session",
    "RUNNING",
    "WAITING_HUMAN",
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
]

__version__ = "0.1.0"
