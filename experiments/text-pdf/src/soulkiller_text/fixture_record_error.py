"""Safe persisted-row failures without source text or local diagnostics."""


class FixtureRecordError(ValueError):
    """Expose a fixed validation category without echoing untrusted record data."""

    def __init__(self, category: str) -> None:
        """Keep the named category accessible without adding input or exception details."""
        self.category = category
        super().__init__(category)
