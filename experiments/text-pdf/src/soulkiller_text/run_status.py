"""Named schedule states, distinct from per-fixture extraction outcomes."""

from enum import StrEnum


class RunStatus(StrEnum):
    """COMPLETE means every scheduled call returned, not that extraction succeeded."""

    COMPLETE = "complete"
    TIME_LIMIT = "time_limit"
    OUTPUT_LIMIT = "output_limit"
    UNSUPPORTED_ENVIRONMENT = "unsupported_environment"
    CANCELLED = "cancelled"
    CLEANUP_FAILURE = "cleanup_failure"
