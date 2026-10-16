"""StubAgent: returns fixed actions looked up by frame id or turn index."""

from __future__ import annotations

import copy
from typing import Any


class StubAgent:
    """A no-network agent driven entirely by a fixture script.

    Lookup order: ``stub.by_frame[<frame id>]`` then ``stub.by_turn[<index>]``.
    If neither matches, emit a failing ``done`` so the session terminates.
    """

    def __init__(self, script: dict[str, Any]) -> None:
        stub = script.get("stub", {})
        self._by_frame: dict[str, Any] = stub.get("by_frame", {})
        self._by_turn: dict[str, Any] = stub.get("by_turn", {})

    def propose(
        self,
        *,
        goal: str,
        turn_index: int,
        screenshot: dict[str, Any],
        frame_id: str,
    ) -> dict[str, Any]:
        actions = self._by_frame.get(frame_id)
        if actions is None:
            actions = self._by_turn.get(str(turn_index))
        if actions is None:
            return {
                "actions": [
                    {
                        "type": "done",
                        "status": "failed",
                        "message": f"stub: no scripted actions for frame {frame_id!r} turn {turn_index}",
                    }
                ]
            }
        return {"actions": copy.deepcopy(actions)}
