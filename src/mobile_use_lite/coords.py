"""Coordinate normalization: 0..999 normalized -> pixels."""

from __future__ import annotations


def norm_to_px(norm: int, size_px: int) -> int:
    """Map a normalized coordinate (0..999) to a pixel index for ``size_px``.

    >>> norm_to_px(0, 1080)
    0
    >>> norm_to_px(999, 1080)
    1079
    >>> norm_to_px(512, 1080)
    553
    >>> norm_to_px(500, 1000)
    500
    """
    return round(norm / 999 * (size_px - 1))


def to_px(x: int, y: int, width_px: int, height_px: int) -> tuple[int, int]:
    """Convert a normalized point to an absolute pixel point."""
    return norm_to_px(x, width_px), norm_to_px(y, height_px)


if __name__ == "__main__":
    import doctest

    failures, _ = doctest.testmod()
    raise SystemExit(1 if failures else 0)
