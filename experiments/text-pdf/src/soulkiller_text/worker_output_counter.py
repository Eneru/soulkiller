"""Focused observation collaborator without retained output or diagnostics."""

from dataclasses import dataclass


@dataclass
class WorkerOutputCounter:
    """Accumulate bytes actually read, including any overflow probe byte."""

    output_bytes: int = 0

    def observe(self, byte_count: int) -> None:
        """Count a consumed stdout or stderr chunk without receiving its contents."""
        self.output_bytes += byte_count
