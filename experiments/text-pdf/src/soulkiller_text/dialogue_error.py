"""Safe public failures for the synthetic answer experiment."""


class DialogueError(ValueError):
    """Carry a fixed category, never raw source, question or model diagnostics."""

    def __init__(self, category: str, *, detail: str | None = None) -> None:
        """Expose fixed categories and details through the CLI error boundary."""
        self.category = category
        self.detail = detail
        super().__init__(category)
