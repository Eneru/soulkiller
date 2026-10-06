"""Stable corpus failures without supplied paths or source content."""


class CorpusError(ValueError):
    """Expose only the named failure category in the exception message."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)
