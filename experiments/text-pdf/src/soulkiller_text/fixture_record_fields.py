"""Strict non-executable JSON and caller-supplied fixture identity validation."""

import json
import re
from typing import Never, cast

from . import fixture_record_constants as constants
from .corpus_constants import MAX_PDF_CORPUS_PAGES
from .corpus_fixture import CorpusFixture
from .fixture_record_error import FixtureRecordError
from .pdf_corpus_fixture import PdfCorpusFixture


def exact_fields(value: object, expected: frozenset[str]) -> dict[str, object]:
    """Require the complete declared object shape before accessing any field."""
    if type(value) is not dict or set(value) != expected:
        raise FixtureRecordError(constants.INVALID_RECORD)
    return cast(dict[str, object], value)


def scalar_text(value: object, *, allow_empty: bool = True) -> str:
    """Retain exact Unicode text while rejecting subclasses and surrogate code points."""
    if (
        type(value) is not str
        or (not allow_empty and not value)
        or any(0xD800 <= ord(character) <= 0xDFFF for character in value)
    ):
        raise FixtureRecordError(constants.INVALID_RECORD)
    return value


def validate_specification(specification: CorpusFixture | PdfCorpusFixture) -> None:
    """Check the supplied identity boundary without claiming source or manifest acceptance."""
    if type(specification) not in (CorpusFixture, PdfCorpusFixture):
        raise FixtureRecordError(constants.INVALID_RECORD)
    fixture_id = scalar_text(specification.fixture_id)
    source_hash = scalar_text(specification.sha256)
    expected_format = "pdf" if type(specification) is PdfCorpusFixture else "txt"
    if (
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", fixture_id) is None
        or re.fullmatch(r"[0-9a-f]{64}", source_hash) is None
        or type(specification.format) is not str
        or specification.format != expected_format
    ):
        raise FixtureRecordError(constants.INVALID_RECORD)
    if isinstance(specification, PdfCorpusFixture) and (
        type(specification.page_count) is not int
        or not 1 <= specification.page_count <= MAX_PDF_CORPUS_PAGES
    ):
        raise FixtureRecordError(constants.INVALID_RECORD)


def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate keys in every JSON object instead of accepting last-write wins."""
    fields: dict[str, object] = {}
    for key, value in pairs:
        if key in fields:
            raise FixtureRecordError(constants.INVALID_RECORD)
        fields[key] = value
    return fields


def _reject_number(value: str) -> Never:
    """Reject floating-point and nonfinite tokens because this schema uses exact integers."""
    raise FixtureRecordError(constants.INVALID_RECORD)


def decode_fields(payload: bytes) -> dict[str, object]:
    """Bound exact input bytes and reject invalid UTF-8, duplicate/deep JSON and extra keys."""
    if type(payload) is not bytes:
        raise FixtureRecordError(constants.INVALID_RECORD)
    if len(payload) > constants.MAX_PAYLOAD_BYTES:
        raise FixtureRecordError(constants.RECORD_TOO_LARGE)
    try:
        fields: object = json.loads(
            payload.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_fields,
            parse_constant=_reject_number,
            parse_float=_reject_number,
        )
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise FixtureRecordError(constants.INVALID_RECORD) from None
    return exact_fields(fields, constants.RECORD_FIELDS)


def encode_fields(fields: dict[str, object]) -> bytes:
    """Emit deterministic compact ASCII JSON, refusing overhead that exceeds the store cap."""
    try:
        payload = json.dumps(
            fields, ensure_ascii=True, allow_nan=False, separators=(",", ":")
        ).encode("ascii")
    except (TypeError, ValueError, RecursionError, UnicodeError):
        raise FixtureRecordError(constants.INVALID_RECORD) from None
    if len(payload) > constants.MAX_PAYLOAD_BYTES:
        raise FixtureRecordError(constants.RECORD_TOO_LARGE)
    return payload
