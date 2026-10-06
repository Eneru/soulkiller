"""Validated, immutable resource guards for the trusted TXT worker."""

from dataclasses import dataclass
from math import isfinite

from .worker_constants import (
    MAX_ADDRESS_SPACE_BYTES,
    MAX_OUTPUT_BYTES,
    MAX_WALL_SECONDS,
    MIN_ADDRESS_SPACE_BYTES,
)


@dataclass(frozen=True)
class WorkerLimits:
    """Allow smaller test budgets without increasing the reviewed ceilings."""

    wall_seconds: float = MAX_WALL_SECONDS
    address_space_bytes: int = MAX_ADDRESS_SPACE_BYTES
    output_bytes: int = MAX_OUTPUT_BYTES

    def __post_init__(self) -> None:
        if (
            isinstance(self.wall_seconds, bool)
            or not isinstance(self.wall_seconds, (int, float))
            or not 0 < self.wall_seconds <= MAX_WALL_SECONDS
            or not isfinite(self.wall_seconds)
        ):
            raise ValueError("invalid_wall_limit")
        if (
            type(self.address_space_bytes) is not int
            or not MIN_ADDRESS_SPACE_BYTES <= self.address_space_bytes <= MAX_ADDRESS_SPACE_BYTES
        ):
            raise ValueError("invalid_memory_limit")
        if type(self.output_bytes) is not int or not 0 < self.output_bytes <= MAX_OUTPUT_BYTES:
            raise ValueError("invalid_output_limit")
