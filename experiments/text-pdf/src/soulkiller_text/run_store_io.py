"""Create-only framed publication and bounded descriptor-based inspection."""

import os
import secrets
import stat

from . import run_store_constants as constants
from .confined_files import read_confined
from .corpus_error import CorpusError
from .run_store_error import RunStoreError
from .run_store_frames import decode_frame


def _scratch_flags() -> int:
    return os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC


def _write_all(descriptor: int, frame: bytes) -> None:
    remaining = memoryview(frame)
    while remaining:
        try:
            written = os.write(descriptor, remaining)
        except InterruptedError:
            continue
        if written <= 0:
            raise RunStoreError(constants.STORAGE_UNAVAILABLE)
        remaining = remaining[written:]


def _verify_owned(root: int, name: str, descriptor: int, size: int, links: int) -> None:
    acquired = os.fstat(descriptor)
    named = os.stat(name, dir_fd=root, follow_symlinks=False)
    expected = (acquired.st_dev, acquired.st_ino, acquired.st_mode, size, links)
    observed = (named.st_dev, named.st_ino, named.st_mode, named.st_size, named.st_nlink)
    if (
        not stat.S_ISREG(acquired.st_mode)
        or acquired.st_size != size
        or acquired.st_nlink != links
        or observed != expected
    ):
        raise RunStoreError(constants.UNSAFE_PATH)


def _publish(root: int, name: str, frame: bytes) -> None:
    scratch = constants.SCRATCH_PREFIX + secrets.token_hex(constants.SCRATCH_TOKEN_BYTES)
    descriptor = os.open(scratch, _scratch_flags(), constants.FILE_MODE, dir_fd=root)
    try:
        _verify_owned(root, scratch, descriptor, size=0, links=1)
        _write_all(descriptor, frame)
        os.fsync(descriptor)
        _verify_owned(root, scratch, descriptor, size=len(frame), links=1)
        os.link(scratch, name, src_dir_fd=root, dst_dir_fd=root, follow_symlinks=False)
        _verify_owned(root, scratch, descriptor, size=len(frame), links=2)
        _verify_owned(root, name, descriptor, size=len(frame), links=2)
        os.unlink(scratch, dir_fd=root)
        os.fsync(root)
    finally:
        os.close(descriptor)


def publish_record(root: int, name: str, frame: bytes) -> None:
    """Never replace a final entry or remove scratch after a failed publication."""
    try:
        _publish(root, name, frame)
    except FileExistsError:
        raise RunStoreError(constants.RECORD_EXISTS) from None
    except OSError:
        raise RunStoreError(constants.STORAGE_UNAVAILABLE) from None


def read_payload(root: int, name: str) -> bytes:
    """A frame digest checks corruption/completeness rather than authenticity."""
    try:
        frame = read_confined(root, name, constants.MAX_RECORD_BYTES)
    except CorpusError as error:
        category = (
            constants.RECORD_UNAVAILABLE
            if error.category == "source_unavailable"
            else constants.INVALID_RECORD
        )
        raise RunStoreError(category) from None
    return decode_frame(frame)
