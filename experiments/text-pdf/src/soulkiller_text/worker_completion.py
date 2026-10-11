"""Classify observed worker completion without changing supervisor lifecycle."""

from .wire_protocol import decode_result
from .worker_constants import MEMORY_FAILURE_EXIT, SUCCESS_EXIT, UNSUPPORTED_EXIT
from .worker_outcome import WorkerOutcome
from .worker_result import WorkerResult


def classify_completion(
    return_code: int | None,
    pipe_failure: WorkerOutcome | None,
    response: bytes,
    source_sha256: str,
) -> WorkerResult:
    """Retain cap/deadline precedence and accept text only after verified completion."""
    if pipe_failure in (WorkerOutcome.TIMEOUT, WorkerOutcome.OUTPUT_LIMIT):
        return WorkerResult(pipe_failure, source_sha256, None)
    if return_code is None:
        return WorkerResult(WorkerOutcome.TIMEOUT, source_sha256, None)
    if return_code == UNSUPPORTED_EXIT:
        return WorkerResult(WorkerOutcome.UNSUPPORTED_ENVIRONMENT, source_sha256, None)
    if return_code == MEMORY_FAILURE_EXIT:
        return WorkerResult(WorkerOutcome.RESOURCE_LIMIT, source_sha256, None)
    if return_code != SUCCESS_EXIT or pipe_failure == WorkerOutcome.CANDIDATE_FAILURE:
        return WorkerResult(WorkerOutcome.CANDIDATE_FAILURE, source_sha256, None)
    try:
        return decode_result(response, source_sha256)
    except ValueError:
        return WorkerResult(WorkerOutcome.PROTOCOL_ERROR, source_sha256, None)
