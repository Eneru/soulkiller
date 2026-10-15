"""Safe storage failures without supplied paths, payloads or OS diagnostics."""


class RunStoreError(ValueError):
    """Expose a stable category rather than local filesystem details."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)
