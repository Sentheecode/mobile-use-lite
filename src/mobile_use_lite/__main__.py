"""CLI entry point: ``python -m mobile_use_lite``."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .agent import StubAgent
from .harness import MockDriver
from .schema import E_SCHEMA, SchemaError, validate_turn
from .session import CANCELLED, FAILED, SUCCEEDED, WAITING_HUMAN, Session

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_SCHEMA = 2
EXIT_CANCELLED = 3
EXIT_WAITING_HUMAN = 4

_ILLEGAL_TURN = {
    "actions": [
        {"type": "teleport", "x": 1, "y": 2},
    ]
}


def _load_script(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _print_turns(session: Session) -> None:
    for turn in session.turns:
        types = ", ".join(a["type"] for a in turn["actions"])
        print(f"  turn {turn['index']}: [{turn['frame_id']}] {types}")
        for action, result in zip(turn["actions"], turn["results"]):
            px = result.get("meta", {}).get("px_x")
            suffix = f" px=({px},{result['meta'].get('px_y')})" if px is not None else ""
            print(f"    - {action['type']} ok={result['ok']}{suffix}")


def _run_illegal_demo() -> int:
    print("feeding illegal action to validate_turn ...")
    try:
        validate_turn(_ILLEGAL_TURN)
    except SchemaError as exc:
        print(f"{E_SCHEMA}: {exc.detail}")
        return EXIT_SCHEMA
    print("unexpected: illegal action was accepted")
    return EXIT_FAILED


def _build_session(args: argparse.Namespace) -> Session:
    script = _load_script(args.script)
    driver = MockDriver(script)
    agent = StubAgent(script)
    goal = args.goal if args.goal is not None else script.get("goal", "")
    return Session(
        goal=goal,
        driver=driver,
        agent=agent,
        max_turns=args.max_turns,
        approve_sensitive=args.approve,
    )


def _exit_code(session: Session) -> int:
    if session.error_code == E_SCHEMA:
        return EXIT_SCHEMA
    return {
        SUCCEEDED: EXIT_OK,
        FAILED: EXIT_FAILED,
        CANCELLED: EXIT_CANCELLED,
        WAITING_HUMAN: EXIT_WAITING_HUMAN,
    }.get(session.status, EXIT_FAILED)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mobile_use_lite",
        description="Mobile-Use Lite P0 stub loop (no network calls).",
    )
    parser.add_argument("--script", help="path to a P0 fixture script JSON")
    parser.add_argument("--goal", help="override the script goal")
    parser.add_argument("--max-turns", type=int, default=20)
    parser.add_argument("--approve", action="store_true", help="auto-approve sensitive steps")
    parser.add_argument("--reject", action="store_true", help="reject a sensitive step -> cancelled")
    parser.add_argument(
        "--illegal-demo",
        action="store_true",
        help="feed an illegal action to the validator and exit non-zero with E_SCHEMA",
    )
    parser.add_argument("--json", action="store_true", help="dump the final session as JSON")
    args = parser.parse_args(argv)

    if args.illegal_demo:
        return _run_illegal_demo()

    if not args.script:
        parser.error("--script is required (or use --illegal-demo)")

    try:
        session = _build_session(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"E_DEVICE: cannot load script: {exc}", file=sys.stderr)
        return EXIT_FAILED

    status = session.run()

    if status == WAITING_HUMAN and args.reject:
        status = session.reject(actor="cli", comment="--reject flag")

    if args.json:
        print(json.dumps(session.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"goal: {session.goal}")
        _print_turns(session)
        if session.pending_sensitive:
            pending = session.pending_sensitive
            print(f"pending_sensitive: {pending['reason']}")
            print(f"  blocked_actions: {json.dumps(pending['blocked_actions'], ensure_ascii=False)}")
        if session.error_code:
            print(f"error: {session.error_code}: {session.error_detail}")
        print(f"status: {status}")
        if status == WAITING_HUMAN:
            print("resume with: --approve (continue) or --reject (cancel)")

    return _exit_code(session)


if __name__ == "__main__":
    raise SystemExit(main())
