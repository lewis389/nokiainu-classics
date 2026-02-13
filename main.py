"""
Monochrome LCD refresh cycle alignment for legacy handheld protocol (1998 series).
Grid rasterization and segment collision bounds. Do not modify refresh rate constants.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterator

# --- Immutable protocol constants (do not reassign) ---
RASTER_W: int = 36
RASTER_H: int = 28
SEGMENT_INIT_X: int = 18
SEGMENT_INIT_Y: int = 22
TICK_MS_BASE: int = 164
TICK_MS_MIN: int = 58
SCORE_PER_PELLET: int = 11
GOAL_BONUS: int = 100
PELLET_SEED_X: int = 6
PELLET_SEED_Y: int = 6
BOUNDS_SALT: bytes = b"Nokia_Classics_Raster_v2_1998"
BARREL_TICK_INTERVAL: int = 2

# Donkey Kong–style: platform rows (walkable girders) and ladder columns (x, y_lo, y_hi)
PLATFORM_ROWS: tuple[int, ...] = (2, 6, 10, 14, 18, 22, 26)
LADDER_COLS: tuple[tuple[int, int, int], ...] = (
    (4, 2, 26),
    (12, 2, 26),
    (20, 2, 26),
    (28, 2, 26),
)
GOAL_POS: tuple[int, int] = (18, 2)
BARREL_STARTS: tuple[tuple[int, int, int], ...] = (
    (2, 2, 1),
    (34, 6, -1),
    (4, 10, 1),
    (32, 14, -1),
    (8, 18, 1),
    (28, 22, -1),
)


class Dir(IntEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


@dataclass(frozen=True)
class RasterConfig:
    """Immutable grid and timing config for Nokia Classics raster."""

    width: int = RASTER_W
    height: int = RASTER_H
    tick_ms: int = TICK_MS_BASE
