"""Open and verify the exact local model without resolving symlinks."""

import hashlib
import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .confined_files import corpus_descriptor
from .corpus_error import CorpusError
from .dialogue_error import DialogueError
from .local_model_constants import MODEL_DIRECTORY
from .local_model_profiles import LocalModelProfile


def _revision(info: os.stat_result) -> tuple[int, int, int]:
    """Identify in-place changes without depending on read-sensitive access time."""
    return info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _verify_asset(stream: int, before: os.stat_result, profile: LocalModelProfile) -> None:
    """Hash at most the approved number of bytes and reject untrusted file types."""
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != profile.size:
        raise DialogueError("invalid_local_model_asset")
    digest = hashlib.sha256()
    remaining = profile.size
    while remaining:
        chunk = os.read(stream, min(1024**2, remaining))
        if not chunk:
            raise DialogueError("invalid_local_model_asset")
        remaining -= len(chunk)
        digest.update(chunk)
    if digest.hexdigest() != profile.sha256 or _revision(before) != _revision(os.fstat(stream)):
        raise DialogueError("invalid_local_model_asset")


@contextmanager
def verified_model(workspace: Path, profile: LocalModelProfile) -> Iterator[int]:
    """Keep the same Linux descriptor open through use; reject concurrent edits."""
    try:
        with corpus_descriptor(workspace, MODEL_DIRECTORY) as directory:
            flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
            stream = os.open(profile.filename, flags, dir_fd=directory)
            try:
                before = os.fstat(stream)
                _verify_asset(stream, before, profile)
                yield stream
                if _revision(before) != _revision(os.fstat(stream)):
                    raise DialogueError("invalid_local_model_asset")
            finally:
                os.close(stream)
    except (CorpusError, OSError):
        raise DialogueError("local_model_asset_unavailable") from None
