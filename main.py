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
