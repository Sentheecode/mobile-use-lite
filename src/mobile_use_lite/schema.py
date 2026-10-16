"""P0 schema loading + validation (stdlib only, no jsonschema dependency).

Authoritative contract lives in ``schemas/action.schema.json`` and
``schemas/turn.schema.json``. This module mirrors those rules in code so the
package works with a bare Python install. If ``jsonschema`` happens to be
installed we cross-check against the JSON files as a safety net.
"""

from __future__ import annotations

import json
import os
from typing import Any

E_SCHEMA = "E_SCHEMA"
E_COORD_RANGE = "E_COORD_RANGE"

ACTION_TYPES = ("click", "swipe", "type", "back", "wait", "done")
SIDE_EFFECT_TYPES = frozenset({"click", "swipe", "type", "back"})

WAIT_CAP_MS = 10000
SWIPE_DEFAULT_MS = 300

_SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schemas")


class SchemaError(ValueError):
    """Raised when an action or turn envelope violates the P0 schema."""

    def __init__(self, detail: str, code: str = E_SCHEMA) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def load_schema(name: str) -> dict[str, Any]:
    """Load a JSON Schema document by file name (e.g. ``action.schema.json``)."""
    path = os.path.join(_SCHEMA_DIR, name)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _coord(action: dict[str, Any], field: str) -> int:
    value = action.get(field)
    if not _is_int(value):
        raise SchemaError(f"{action.get('type')}.{field} must be an integer in 0..999")
    if not 0 <= value <= 999:
        raise SchemaError(
            f"{action.get('type')}.{field}={value} out of range 0..999", code=E_COORD_RANGE
        )
    return value


def _reason(action: dict[str, Any]) -> None:
    if "reason" in action and not isinstance(action["reason"], str):
        raise SchemaError(f"{action.get('type')}.reason must be a string")


def _reject_unknown(action: dict[str, Any], allowed: set[str]) -> None:
    extra = set(action) - allowed
    if extra:
        raise SchemaError(f"{action.get('type')} has unknown field(s): {sorted(extra)}")


def _positive_int(action: dict[str, Any], field: str, *, cap: int | None = None) -> int:
    value = action.get(field)
    if not _is_int(value) or value < 1:
        raise SchemaError(f"{action.get('type')}.{field} must be a positive integer")
    if cap is not None and value > cap:
        raise SchemaError(f"{action.get('type')}.{field}={value} exceeds cap {cap}")
    return value


def validate_action(action: Any) -> dict[str, Any]:
    """Validate one action and return a normalized copy.

    Raises :class:`SchemaError` (code ``E_SCHEMA`` or ``E_COORD_RANGE``).
    Normalization fills defaults (``swipe.duration_ms``) and the ``wait.ms`` alias.
    """
    if not isinstance(action, dict):
        raise SchemaError("action must be a JSON object")

    action_type = action.get("type")
    if action_type not in ACTION_TYPES:
        raise SchemaError(f"unknown action type: {action_type!r}")

    _reason(action)
    out: dict[str, Any] = {"type": action_type}
    if "reason" in action:
        out["reason"] = action["reason"]

    if action_type == "click":
        _reject_unknown(action, {"type", "x", "y", "reason"})
        out["x"] = _coord(action, "x")
        out["y"] = _coord(action, "y")

    elif action_type == "swipe":
        _reject_unknown(action, {"type", "x1", "y1", "x2", "y2", "duration_ms", "reason"})
        out["x1"] = _coord(action, "x1")
        out["y1"] = _coord(action, "y1")
        out["x2"] = _coord(action, "x2")
        out["y2"] = _coord(action, "y2")
        if "duration_ms" in action:
            out["duration_ms"] = _positive_int(action, "duration_ms")
        else:
            out["duration_ms"] = SWIPE_DEFAULT_MS

    elif action_type == "type":
        _reject_unknown(action, {"type", "text", "reason"})
        if not isinstance(action.get("text"), str):
            raise SchemaError("type.text must be a string")
        out["text"] = action["text"]

    elif action_type == "back":
        _reject_unknown(action, {"type", "reason"})

    elif action_type == "wait":
        _reject_unknown(action, {"type", "duration_ms", "ms", "reason"})
        if "duration_ms" in action:
            out["duration_ms"] = _positive_int(action, "duration_ms", cap=WAIT_CAP_MS)
        elif "ms" in action:
            out["duration_ms"] = _positive_int(action, "ms", cap=WAIT_CAP_MS)
        else:
            raise SchemaError("wait requires duration_ms (alias: ms)")

    elif action_type == "done":
        _reject_unknown(action, {"type", "success", "status", "message", "reason"})
        if "success" not in action and "status" not in action:
            raise SchemaError("done requires success (bool) or status ('succeeded'|'failed')")
        if "success" in action and not isinstance(action["success"], bool):
            raise SchemaError("done.success must be a boolean")
        if "status" in action and action["status"] not in ("succeeded", "failed"):
            raise SchemaError("done.status must be 'succeeded' or 'failed'")
        if "success" in action:
            out["success"] = action["success"]
        if "status" in action:
            out["status"] = action["status"]
        if "message" in action:
            if not isinstance(action["message"], str):
                raise SchemaError("done.message must be a string")
            out["message"] = action["message"]

    return out


def validate_turn(turn: Any) -> dict[str, Any]:
    """Validate an agent turn envelope; any invalid action rejects the whole turn.

    Envelope shape: ``{"actions": Action[], "sensitive_hint": bool?, "notes": str?}``.
    ``done`` (if present) must be the last action. Raises ``SchemaError`` with
    code ``E_SCHEMA``.
    """
    if not isinstance(turn, dict):
        raise SchemaError("turn must be a JSON object")

    extra = set(turn) - {"actions", "sensitive_hint", "notes"}
    if extra:
        raise SchemaError(f"turn has unknown field(s): {sorted(extra)}")

    actions = turn.get("actions")
    if not isinstance(actions, list) or not actions:
        raise SchemaError("turn.actions must be a non-empty array")

    if "sensitive_hint" in turn and not isinstance(turn["sensitive_hint"], bool):
        raise SchemaError("turn.sensitive_hint must be a boolean")
    if "notes" in turn and not isinstance(turn["notes"], str):
        raise SchemaError("turn.notes must be a string")

    normalized: list[dict[str, Any]] = []
    for index, action in enumerate(actions):
        try:
            normalized.append(validate_action(action))
        except SchemaError as exc:
            raise SchemaError(f"actions[{index}]: {exc.detail}", code=E_SCHEMA) from exc

    for index, action in enumerate(normalized):
        if action["type"] == "done" and index != len(normalized) - 1:
            raise SchemaError("done must be the last action in a turn")

    out: dict[str, Any] = {"actions": normalized}
    if "sensitive_hint" in turn:
        out["sensitive_hint"] = turn["sensitive_hint"]
    if "notes" in turn:
        out["notes"] = turn["notes"]
    return out
