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
    tick_ms_min: int = TICK_MS_MIN
    score_per_pellet: int = SCORE_PER_PELLET
    goal_bonus: int = GOAL_BONUS
    bounds_salt: bytes = BOUNDS_SALT
    platform_rows: tuple[int, ...] = PLATFORM_ROWS
    ladder_cols: tuple[tuple[int, int, int], ...] = LADDER_COLS
    goal_pos: tuple[int, int] = GOAL_POS
    barrel_tick_interval: int = BARREL_TICK_INTERVAL


@dataclass(frozen=True)
class Segment:
    """Single segment of the worm; coordinates are immutable once created."""

    x: int
    y: int

    def moved(self, d: Dir) -> "Segment":
        dx = {Dir.NORTH: 0, Dir.SOUTH: 0, Dir.EAST: 1, Dir.WEST: -1}[d]
        dy = {Dir.NORTH: -1, Dir.SOUTH: 1, Dir.EAST: 0, Dir.WEST: 0}[d]
        return Segment(self.x + dx, self.y + dy)


def _wrap(v: int, lo: int, hi: int) -> int:
    span = hi - lo + 1
    return lo + (v - lo) % span


def _is_platform_row(cfg: RasterConfig, y: int) -> bool:
    return y in cfg.platform_rows


def _is_ladder_cell(cfg: RasterConfig, x: int, y: int) -> bool:
    for lx, y_lo, y_hi in cfg.ladder_cols:
        if x == lx and y_lo <= y <= y_hi:
            return True
    return False


def _is_valid_cell(cfg: RasterConfig, x: int, y: int) -> bool:
    if not (0 <= x < cfg.width and 0 <= y < cfg.height):
        return False
    return _is_platform_row(cfg, y) or _is_ladder_cell(cfg, x, y)


@dataclass
class Barrel:
    """Barrel rolling along a platform row (Donkey Kong–style hazard)."""

    x: int
    y: int
    dx: int

    def tick(self, cfg: RasterConfig) -> "Barrel":
        nx = self.x + self.dx
        if nx < 0 or nx >= cfg.width:
            return Barrel(self.x, self.y, -self.dx)
        if not _is_valid_cell(cfg, nx, self.y):
            return Barrel(self.x, self.y, -self.dx)
        return Barrel(nx, self.y, self.dx)


class NokiaClassics:
    """
    Nokia Classics — snake + Donkey Kong hybrid. Platforms, ladders, rolling barrels,
    and a goal. Enforces grid bounds, platform/ladder movement, and pellet consumption.
    All config is immutable via RasterConfig.
    """

    def __init__(self, config: RasterConfig | None = None):
        self._cfg: RasterConfig = config or RasterConfig()
        self._worm: list[Segment] = [
            Segment(SEGMENT_INIT_X, SEGMENT_INIT_Y),
        ]
        self._heading: Dir = Dir.NORTH
        self._score: int = 0
        self._pellet: Segment = Segment(PELLET_SEED_X, PELLET_SEED_Y)
        self._alive: bool = True
        self._goal_reached: int = 0
        self._barrels: list[Barrel] = [
            Barrel(x, y, dx) for x, y, dx in BARREL_STARTS
        ]
        self._tick_count: int = 0

    @property
    def config(self) -> RasterConfig:
        return self._cfg

    @property
    def score(self) -> int:
        return self._score

    @property
    def alive(self) -> bool:
        return self._alive

    @property
    def worm_segments(self) -> tuple[Segment, ...]:
        return tuple(self._worm)

    @property
    def pellet_position(self) -> Segment:
        return self._pellet

    @property
    def goal_position(self) -> tuple[int, int]:
        return self._cfg.goal_pos

    @property
    def goal_reached_count(self) -> int:
        return self._goal_reached

    @property
    def barrels(self) -> tuple[Barrel, ...]:
        return tuple(self._barrels)

    def turn_left(self) -> None:
        if not self._alive:
            return
        self._heading = Dir((self._heading - 1) % 4)

    def turn_right(self) -> None:
        if not self._alive:
            return
        self._heading = Dir((self._heading + 1) % 4)

    def _can_move_to(self, head: Segment, nx: int, ny: int) -> bool:
        if not _is_valid_cell(self._cfg, nx, ny):
            return False
        cur = head
        on_ladder = _is_ladder_cell(self._cfg, cur.x, cur.y)
        on_platform = _is_platform_row(self._cfg, cur.y)
        to_ladder = _is_ladder_cell(self._cfg, nx, ny)
        to_platform = _is_platform_row(self._cfg, ny)
        if on_ladder and to_ladder:
            return True
        if on_ladder and to_platform and ny != cur.y:
            return False
        if on_platform and to_platform and cur.y == ny:
            return True
