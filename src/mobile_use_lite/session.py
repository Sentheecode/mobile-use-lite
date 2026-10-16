"""Session state machine with the P0 sensitive gate."""

from __future__ import annotations

import re
from typing import Any

from .schema import E_SCHEMA, SIDE_EFFECT_TYPES, SchemaError, validate_turn

RUNNING = "running"
WAITING_HUMAN = "waiting_human"
SUCCEEDED = "succeeded"
FAILED = "failed"
CANCELLED = "cancelled"

TERMINAL = frozenset({SUCCEEDED, FAILED, CANCELLED})

_SENSITIVE_GOAL_RE = re.compile(r"登录|支付|验证码|password|login|pay", re.IGNORECASE)


def sensitive_goal_keyword(goal: str) -> str | None:
    """Return the first sensitive keyword found in the goal, if any."""
    match = _SENSITIVE_GOAL_RE.search(goal or "")
    return match.group(0) if match else None


def _mask(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    masked: list[dict[str, Any]] = []
    for action in actions:
        item = dict(action)
        if item.get("type") == "type":
            item["text"] = "***"
        masked.append(item)
    return masked


class Session:
    """Drives agent -> gate -> harness until a terminal state."""

    def __init__(
        self,
        *,
        goal: str,
        driver: Any,
        agent: Any,
        max_turns: int = 20,
        approve_sensitive: bool = False,
    ) -> None:
        self.goal = goal
        self.driver = driver
        self.agent = agent
        self.max_turns = max_turns
        self.approve_sensitive = approve_sensitive

        self.status = RUNNING
        self.turn_count = 0
        self.error_code: str | None = None
        self.error_detail: str | None = None
        self.pending_sensitive: dict[str, Any] | None = None
        self.human_decision: dict[str, Any] | None = None
        self.turns: list[dict[str, Any]] = []
        self.last_screenshot: dict[str, Any] | None = None

        self._pending: dict[str, Any] | None = None
        self._gate_reasons: list[str] = []

    # -- turn plumbing -----------------------------------------------------

    def _begin_turn(self) -> None:
        self.turn_count += 1
        screenshot = self.driver.screenshot()
        frame = self.driver.current_frame()
        self.last_screenshot = screenshot

        try:
            proposed = self.agent.propose(
                goal=self.goal,
                turn_index=self.turn_count,
                screenshot=screenshot,
                frame_id=frame.get("id", ""),
            )
            turn = validate_turn(proposed)
        except SchemaError as exc:
            self._fail(exc.code, exc.detail)
            return

        self._pending = {"turn": turn, "frame": frame, "screenshot": screenshot}
        self._gate_reasons = self._collect_gate_reasons(turn, frame)

    def _collect_gate_reasons(self, turn: dict[str, Any], frame: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        if frame.get("sensitive"):
            reasons.append("heuristic:frame_sensitive")
        if turn.get("sensitive_hint"):
            reasons.append("heuristic:agent_hint")
        keyword = sensitive_goal_keyword(self.goal)
        if keyword:
            reasons.append(f"heuristic:goal_keyword:{keyword}")
        return reasons

    def _pending_side_effects(self) -> list[dict[str, Any]]:
        if not self._pending:
            return []
        return [a for a in self._pending["turn"]["actions"] if a["type"] in SIDE_EFFECT_TYPES]

    def _execute_pending(self) -> None:
        assert self._pending is not None
        turn = self._pending["turn"]
        frame = self._pending["frame"]
        screenshot = self._pending["screenshot"]
        actions = turn["actions"]

        non_terminal = [a for a in actions if a["type"] != "done"]
        outcome = self.driver.execute(non_terminal)
        self.turns.append(
            {
                "index": self.turn_count,
                "frame_id": frame.get("id"),
                "actions": actions,
                "results": outcome["results"],
                "screenshot_after": outcome["screenshot"]["screenshot_ref"],
            }
        )
        self.last_screenshot = outcome["screenshot"]

        done = next((a for a in actions if a["type"] == "done"), None)
        self._pending = None
        self._gate_reasons = []
        if done is not None:
            ok = done.get("success") is True or done.get("status") == "succeeded"
            if ok:
                self.status = SUCCEEDED
            else:
                self._fail("E_DONE_FAILED", done.get("message") or "done marked failure")

    def _fail(self, code: str, detail: str) -> None:
        self.status = FAILED
        self.error_code = code
        self.error_detail = detail
        self._pending = None
        self._gate_reasons = []

    # -- public API --------------------------------------------------------

    def run(self) -> str:
        """Run until terminal state or until a human decision is required."""
        while self.status == RUNNING:
            if self.turn_count >= self.max_turns:
                self._fail("E_MAX_TURNS", f"exceeded max_turns={self.max_turns}")
                break

            self._begin_turn()
            if self.status != RUNNING:
                break

            if self._gate_reasons:
                self.status = WAITING_HUMAN
                side_effects = self._pending_side_effects()
                self.pending_sensitive = {
                    "reason": ", ".join(self._gate_reasons),
                    "blocked_actions": _mask(side_effects),
                    "screenshot_ref": self._pending["screenshot"]["screenshot_ref"],
                }
                if self.approve_sensitive:
                    self.approve(actor="cli", comment="--approve flag")
                else:
                    break
            else:
                self._execute_pending()

        return self.status

    def approve(self, actor: str = "human", comment: str = "") -> str:
        """Approve a pending sensitive step and resume execution."""
        if self.status != WAITING_HUMAN:
            return self.status
        self.human_decision = {
            "decision": "approve",
            "actor": actor,
            "comment": comment,
        }
        self.pending_sensitive = None
        self.status = RUNNING
        self._execute_pending()
        return self.run()

    def reject(self, actor: str = "human", comment: str = "") -> str:
        """Reject a pending sensitive step -> cancelled."""
        if self.status != WAITING_HUMAN:
            return self.status
        self.human_decision = {
            "decision": "reject",
            "actor": actor,
            "comment": comment,
        }
        self.pending_sensitive = None
        self.status = CANCELLED
        self.error_code = "E_CANCELLED"
        return self.status

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "status": self.status,
            "turn_count": self.turn_count,
            "max_turns": self.max_turns,
            "error_code": self.error_code,
            "error_detail": self.error_detail,
            "pending_sensitive": self.pending_sensitive,
            "human_decision": self.human_decision,
            "last_screenshot_ref": (self.last_screenshot or {}).get("screenshot_ref"),
            "turns": self.turns,
        }
