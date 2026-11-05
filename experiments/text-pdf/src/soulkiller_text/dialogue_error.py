"""Safe public failures for the synthetic answer experiment."""


class DialogueError(ValueError):
    """Carry a fixed category, never raw source, question or model diagnostics."""

    def __init__(self, category: str) -> None:
        """Expose only caller-supplied fixed categories through the CLI error boundary."""
        self.category = category
        super().__init__(category)
