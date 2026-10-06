"""Linux descriptor-anchored, read-only snapshots for synthetic inputs."""

import errno
import os
import stat
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .corpus_error import CorpusError
from .corpus_paths import validate_relative_path

CHUNK_BYTES = 64 * 1024


def _directory_flags() -> int:
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def _open_directory(parent: int, name: str) -> int:
    return os.open(name, _directory_flags(), dir_fd=parent)


def _open_leaf(parent: int, name: str) -> int:
    return os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=parent)


def _io_error(error: OSError) -> CorpusError:
    category = (
        "unsafe_file" if error.errno in {errno.ELOOP, errno.ENOTDIR} else "source_unavailable"
    )
    return CorpusError(category)


@contextmanager
def _directory(parent: int, parts: tuple[str, ...]) -> Iterator[int]:
    current = os.dup(parent)
    try:
        for part in parts:
            child = _open_directory(current, part)
            previous = current
            current = child
            os.close(previous)
        yield current
    finally:
        os.close(current)


@contextmanager
def corpus_descriptor(workspace_root: Path, corpus_path: str) -> Iterator[int]:
    """The caller supplies the trusted workspace; manifest data cannot choose it."""
    required = ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK", "O_CLOEXEC")
    if sys.platform != "linux" or not all(hasattr(os, flag) for flag in required):
        raise CorpusError("unsupported_platform")
    if os.open not in os.supports_dir_fd:
        raise CorpusError("unsupported_platform")
    if not workspace_root.is_absolute() or ".." in workspace_root.parts:
        raise CorpusError("invalid_path")
    parts = validate_relative_path(corpus_path)
    try:
        root = os.open("/", _directory_flags())
        try:
            with _directory(root, workspace_root.parts[1:]) as workspace:
                with _directory(workspace, parts) as corpus:
                    yield corpus
        finally:
            os.close(root)
    except OSError as error:
        raise _io_error(error) from None


def _revision(info: os.stat_result) -> tuple[int, ...]:
    # Reading may change atime, so it is deliberately absent from this comparison.
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def read_confined(root: int, relative_path: str, maximum: int) -> bytes:
    """Read one acquired descriptor; never reopen a resolved absolute pathname."""
    parts = validate_relative_path(relative_path)
    try:
        with _directory(root, parts[:-1]) as parent:
            descriptor = _open_leaf(parent, parts[-1])
            try:
                before = os.fstat(descriptor)
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                    raise CorpusError("unsafe_file")
                if before.st_size > maximum:
                    raise CorpusError("input_too_large")
                chunks: list[bytes] = []
                count = 0
                while count <= maximum:
                    chunk = os.read(descriptor, min(CHUNK_BYTES, maximum + 1 - count))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    count += len(chunk)
                if count > maximum:
                    raise CorpusError("input_too_large")
                after = os.fstat(descriptor)
                if _revision(before) != _revision(after) or count != before.st_size:
                    raise CorpusError("source_changed")
                return b"".join(chunks)
            finally:
                os.close(descriptor)
    except OSError as error:
        raise _io_error(error) from None
