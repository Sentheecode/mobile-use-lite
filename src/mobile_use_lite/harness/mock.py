"""MockDriver: replays a scripted list of frames."""

from __future__ import annotations

from typing import Any

from .. import coords
from ..schema import SIDE_EFFECT_TYPES


class MockDriver:
    """A deterministic driver backed by a fixture script.

    The script carries ``frames`` (each ``{id, sensitive, image?}``) and device
    dimensions. Executing a side-effect action advances to the next frame.
    """

    def __init__(self, script: dict[str, Any]) -> None:
        self._script = script
        device = script.get("device", {})
        self._platform = device.get("platform", "mock")
        self._width = int(device.get("width_px", 1080))
        self._height = int(device.get("height_px", 2400))
        self._serial = device.get("serial")
        frames = script.get("frames")
        if not isinstance(frames, list) or not frames:
            raise ValueError("script.frames must be a non-empty list")
        self._frames = frames
        self._index = 0

    @property
    def frame_index(self) -> int:
        return self._index

    def device_info(self) -> dict[str, Any]:
        info = {"platform": self._platform, "width_px": self._width, "height_px": self._height}
        if self._serial:
            info["serial"] = self._serial
        return info

    def current_frame(self) -> dict[str, Any]:
        return self._frames[min(self._index, len(self._frames) - 1)]

    def screenshot(self) -> dict[str, Any]:
        frame = self.current_frame()
        return {
            "screenshot_ref": frame.get("image", f"fixtures/p0/{frame.get('id', 'frame')}.png"),
            "width_px": self._width,
            "height_px": self._height,
            "source": "mock",
        }

    def _advance(self) -> None:
        if self._index < len(self._frames) - 1:
            self._index += 1

    def execute(self, actions: list[dict[str, Any]]) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for action in actions:
            action_type = action.get("type")
            if action_type == "done":
                continue
            meta: dict[str, Any] = {}
            if action_type == "click":
                px = coords.to_px(action["x"], action["y"], self._width, self._height)
                meta = {"px_x": px[0], "px_y": px[1]}
            elif action_type == "swipe":
                meta = {
                    "px": [
                        list(coords.to_px(action["x1"], action["y1"], self._width, self._height)),
                        list(coords.to_px(action["x2"], action["y2"], self._width, self._height)),
                    ],
                    "duration_ms": action["duration_ms"],
                }
            results.append({"ok": True, "error_code": None, "message": None, "meta": meta})
            if action_type in SIDE_EFFECT_TYPES:
                self._advance()
        return {"results": results, "screenshot": self.screenshot()}
