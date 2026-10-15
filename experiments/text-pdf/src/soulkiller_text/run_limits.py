"""Validated immutable aggregate guards for a sequential corpus run."""

from dataclasses import dataclass
from math import isfinite

from .run_constants import MAX_RUN_OUTPUT_BYTES, MAX_RUN_WALL_SECONDS
from .worker_limits import WorkerLimits


@dataclass(frozen=True)
class RunLimits:
    """Allow smaller experimental guards without raising reviewed ceilings."""

    wall_seconds: float = MAX_RUN_WALL_SECONDS
    output_bytes: int = MAX_RUN_OUTPUT_BYTES
    worker_limits: WorkerLimits = WorkerLimits()

    def __post_init__(self) -> None:
        if (
            isinstance(self.wall_seconds, bool)
            or not isinstance(self.wall_seconds, (int, float))
            or not 0 < self.wall_seconds <= MAX_RUN_WALL_SECONDS
            or not isfinite(self.wall_seconds)
        ):
            raise ValueError("invalid_run_wall_limit")
        if type(self.output_bytes) is not int or not 0 < self.output_bytes <= MAX_RUN_OUTPUT_BYTES:
            raise ValueError("invalid_run_output_limit")
        if type(self.worker_limits) is not WorkerLimits:
            raise ValueError("invalid_run_worker_limits")
        WorkerLimits(
            wall_seconds=self.worker_limits.wall_seconds,
            address_space_bytes=self.worker_limits.address_space_bytes,
            output_bytes=self.worker_limits.output_bytes,
        )
