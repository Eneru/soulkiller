"""Linux directory descriptors for a fixed new source-disjoint run namespace."""

import errno
import os
import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from . import run_store_constants as constants
from .confined_files import _directory, _directory_flags
from .corpus_error import CorpusError
from .corpus_paths import validate_relative_path
from .run_store_error import RunStoreError

Identity = tuple[int, int]


def validate_name(value: str) -> None:
    """Accept only the public lowercase ASCII leaf-name grammar."""
    if type(value) is not str or re.fullmatch(constants.NAME_PATTERN, value) is None:
        raise RunStoreError(constants.INVALID_NAME)


def _require_capabilities() -> None:
    flags = ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK", "O_CLOEXEC")
    operations = (os.open, os.mkdir, os.link, os.unlink, os.stat)
    if (
        sys.platform != "linux"
        or not all(hasattr(os, flag) for flag in flags)
        or not all(operation in os.supports_dir_fd for operation in operations)
        or not all(operation in os.supports_follow_symlinks for operation in (os.link, os.stat))
        or not callable(getattr(os, "fsync", None))
    ):
        raise RunStoreError(constants.UNSUPPORTED_PLATFORM)


def _identity(descriptor: int) -> Identity:
    info = os.fstat(descriptor)
    return info.st_dev, info.st_ino


def _source_parts(corpus_path: str) -> tuple[str, ...]:
    try:
        parts = validate_relative_path(corpus_path)
    except CorpusError:
        raise RunStoreError(constants.INVALID_PATH) from None
    output = constants.OUTPUT_PARTS
    if parts[: len(output)] == output or output[: len(parts)] == parts:
        raise RunStoreError(constants.SOURCE_OVERLAP)
    return parts


@contextmanager
def _workspace(workspace_root: Path) -> Iterator[int]:
    if (
        not isinstance(workspace_root, Path)
        or not workspace_root.is_absolute()
        or ".." in workspace_root.parts
    ):
        raise RunStoreError(constants.INVALID_PATH)
    root = os.open("/", _directory_flags())
    try:
        with _directory(root, workspace_root.parts[1:]) as descriptor:
            yield descriptor
    finally:
        os.close(root)


def _chain(workspace: int, parts: tuple[str, ...], *, missing: bool) -> tuple[Identity, ...]:
    current = os.dup(workspace)
    try:
        identities = [_identity(current)]
        for part in parts:
            try:
                child = os.open(part, _directory_flags(), dir_fd=current)
            except FileNotFoundError:
                if missing:
                    break
                raise RunStoreError(constants.SOURCE_UNAVAILABLE) from None
            previous = current
            current = child
            os.close(previous)
            identities.append(_identity(current))
        return tuple(identities)
    finally:
        os.close(current)


def _validate_separation(workspace: int, parts: tuple[str, ...]) -> None:
    source = _chain(workspace, parts, missing=False)
    output = _chain(workspace, constants.OUTPUT_PARTS, missing=True)
    output_complete = len(output) == len(constants.OUTPUT_PARTS) + 1
    if source[-1] in output or (output_complete and output[-1] in source):
        raise RunStoreError(constants.SOURCE_OVERLAP)


@contextmanager
def _output_parent(workspace: int, *, create: bool) -> Iterator[int]:
    current = os.dup(workspace)
    try:
        for part in constants.OUTPUT_PARTS:
            try:
                child = os.open(part, _directory_flags(), dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, constants.DIRECTORY_MODE, dir_fd=current)
                os.fsync(current)
                child = os.open(part, _directory_flags(), dir_fd=current)
            previous = current
            current = child
            os.close(previous)
        yield current
    finally:
        os.close(current)


def _acquire_leaf(parent: int, name: str, *, create: bool) -> int:
    if create:
        try:
            os.mkdir(name, constants.DIRECTORY_MODE, dir_fd=parent)
        except FileExistsError:
            raise RunStoreError(constants.RUN_EXISTS) from None
        os.fsync(parent)
    return os.open(name, _directory_flags(), dir_fd=parent)


def acquire_run(workspace_root: Path, corpus_path: str, run_id: str, *, create: bool) -> int:
    """Create or acquire a run only after source and directory safety checks."""
    _require_capabilities()
    validate_name(run_id)
    parts = _source_parts(corpus_path)
    descriptor: int | None = None
    try:
        with _workspace(workspace_root) as workspace:
            _validate_separation(workspace, parts)
            with _output_parent(workspace, create=create) as parent:
                descriptor = _acquire_leaf(parent, run_id, create=create)
        return descriptor
    except BaseException as error:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                if not isinstance(error, Exception):
                    raise error from None
                raise RunStoreError(constants.STORAGE_UNAVAILABLE) from None
        if not isinstance(error, OSError):
            raise
        category = (
            constants.UNSAFE_PATH
            if error.errno in {errno.ELOOP, errno.ENOTDIR}
            else constants.STORAGE_UNAVAILABLE
        )
        raise RunStoreError(category) from None
