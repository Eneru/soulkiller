"""Bounded non-executable frames for complete opaque record inspection."""

import hmac
import struct
from hashlib import sha256

from . import run_store_constants as constants
from .run_store_error import RunStoreError


def encode_frame(payload: bytes) -> bytes:
    """Validate encoded size before copying or writing the supplied bytes."""
    if type(payload) is not bytes:
        raise RunStoreError(constants.INVALID_PAYLOAD)
    if len(payload) + constants.HEADER_BYTES > constants.MAX_RECORD_BYTES:
        raise RunStoreError(constants.RECORD_TOO_LARGE)
    length = struct.pack("!Q", len(payload))
    return constants.MAGIC + length + sha256(payload).digest() + payload


def decode_frame(frame: bytes) -> bytes:
    """Reject incomplete or corrupted bytes without interpreting their payload."""
    if (
        type(frame) is not bytes
        or not constants.HEADER_BYTES <= len(frame) <= constants.MAX_RECORD_BYTES
        or not frame.startswith(constants.MAGIC)
    ):
        raise RunStoreError(constants.INVALID_RECORD)
    length_end = len(constants.MAGIC) + constants.LENGTH_BYTES
    length = struct.unpack("!Q", frame[len(constants.MAGIC) : length_end])[0]
    payload = frame[constants.HEADER_BYTES :]
    digest = frame[length_end : constants.HEADER_BYTES]
    if length != len(payload) or not hmac.compare_digest(digest, sha256(payload).digest()):
        raise RunStoreError(constants.INVALID_RECORD)
    return payload
