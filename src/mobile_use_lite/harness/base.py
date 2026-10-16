"""Harness driver protocol (P0)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Driver(Protocol):
    """Execution backend: reports device info, captures screens, runs actions."""

    def device_info(self) -> dict[str, Any]:
        """Return ``{platform, width_px, height_px, serial?}``."""

    def screenshot(self) -> dict[str, Any]:
        """Return a ScreenshotRef: ``{screenshot_ref, width_px, height_px, source}``."""

    def current_frame(self) -> dict[str, Any]:
        """Return the current frame metadata ``{id, sensitive, image?}``."""

    def execute(self, actions: list[dict[str, Any]]) -> dict[str, Any]:
        """Run non-terminal actions; return ``{results, screenshot}``."""
