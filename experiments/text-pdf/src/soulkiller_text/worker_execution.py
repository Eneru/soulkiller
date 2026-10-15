"""Immutable completed worker evidence and observed transport consumption."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkerExecution[T]:
    """Retain the existing result alongside actual combined pipe bytes read."""

    result: T
    output_bytes: int
