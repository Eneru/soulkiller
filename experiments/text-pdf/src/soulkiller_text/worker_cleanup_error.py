"""A distinct error when worker termination cannot be confirmed."""


class WorkerCleanupError(RuntimeError):
    """Stop a calling sequence rather than disguise failed cleanup as a result."""

    def __init__(self) -> None:
        super().__init__("worker_cleanup_failed")
