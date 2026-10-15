"""A context-managed opaque run store; no runner or report interpretation."""

import os
from pathlib import Path
from types import TracebackType

from . import run_store_constants as constants
from .run_store_error import RunStoreError
from .run_store_frames import encode_frame
from .run_store_io import publish_record, read_payload
from .run_store_paths import acquire_run, validate_name


class RunStore:
    """Own one acquired directory with bounded create-only or read-only access."""

    def __init__(self, descriptor: int, *, writable: bool) -> None:
        self._descriptor: int | None = descriptor
        self._writable = writable
        self._poisoned = False
        self._record_count = 0
        self._encoded_bytes = 0

    def __enter__(self) -> "RunStore":
        self._open_descriptor()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _open_descriptor(self) -> int:
        if self._descriptor is None:
            raise RunStoreError(constants.CLOSED)
        return self._descriptor

    def write_record(self, name: str, payload: bytes) -> None:
        """Invalid input consumes no scratch; failed publication poisons writes."""
        descriptor = self._open_descriptor()
        if not self._writable:
            raise RunStoreError(constants.READ_ONLY)
        if self._poisoned:
            raise RunStoreError(constants.WRITE_FAILED)
        validate_name(name)
        frame = encode_frame(payload)
        if self._record_count >= constants.MAX_RECORDS:
            raise RunStoreError(constants.RECORD_LIMIT)
        if self._encoded_bytes + len(frame) > constants.MAX_STORE_BYTES:
            raise RunStoreError(constants.STORE_LIMIT)
        self._poisoned = True
        publish_record(descriptor, name, frame)
        self._record_count += 1
        self._encoded_bytes += len(frame)
        self._poisoned = False

    def read_record(self, name: str) -> bytes:
        """Return only bounded complete records, including after a failed write."""
        descriptor = self._open_descriptor()
        validate_name(name)
        return read_payload(descriptor, name)

    def close(self) -> None:
        """Release the owned descriptor once; retain all run and scratch files."""
        descriptor = self._descriptor
        self._descriptor = None
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                raise RunStoreError(constants.STORAGE_UNAVAILABLE) from None


def create_run_store(workspace_root: Path, corpus_path: str, run_id: str) -> RunStore:
    """Create a new run only; never acquire an existing directory for writing."""
    return RunStore(acquire_run(workspace_root, corpus_path, run_id, create=True), writable=True)


def open_run_store(workspace_root: Path, corpus_path: str, run_id: str) -> RunStore:
    """Acquire an existing source-disjoint run without creating any state."""
    return RunStore(acquire_run(workspace_root, corpus_path, run_id, create=False), writable=False)
