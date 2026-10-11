"""Shared strict manifest fields, JSON decoding and metadata validation."""

import json
import re
from collections.abc import Iterable
from typing import Literal, Never, cast

from .corpus_constants import MAX_ANNOTATIONS, MAX_FIXTURES, MAX_MANIFEST_BYTES
from .corpus_error import CorpusError
from .corpus_paths import validate_relative_path

FIXTURE_FIELDS = frozenset(
    (
        "id",
        "path",
        "sha256",
        "format",
        "language",
        "author_label",
        "subject_label",
        "outcome",
        "annotations",
    )
)
_ROOT_FIELDS = frozenset(("schema_version", "fixtures"))


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CorpusError("invalid_manifest")
        result[key] = value
    return result


def _reject_constant(value: str) -> Never:
    raise CorpusError("invalid_manifest")


def exact_fields(value: object, expected: frozenset[str]) -> dict[str, object]:
    """Require exactly the declared keys before accessing their values."""
    if not isinstance(value, dict) or set(value) != expected:
        raise CorpusError("invalid_manifest")
    return cast(dict[str, object], value)


def nonempty_text(value: object, maximum: int | None = None) -> str:
    """Retain literal text while rejecting missing values and surrogate points."""
    if (
        not isinstance(value, str)
        or not value
        or (maximum is not None and len(value) > maximum)
        or any(0xD800 <= ord(character) <= 0xDFFF for character in value)
    ):
        raise CorpusError("invalid_manifest")
    return value


def nonnegative_integer(value: object) -> int:
    """Booleans and numeric coercion are not valid manifest integers."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CorpusError("invalid_manifest")
    return value


def parse_fixture_metadata(
    fields: dict[str, object], expected_format: Literal["txt", "pdf"]
) -> tuple[str, str, str, Literal["fr", "en"], str, str]:
    """Validate common identity, confinement, revision and literal label fields."""
    fixture_id = nonempty_text(fields["id"])
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", fixture_id) is None:
        raise CorpusError("invalid_manifest")

    path = fields["path"]
    if not isinstance(path, str):
        raise CorpusError("invalid_path")
    validate_relative_path(path)
    if path == "manifest.json":
        raise CorpusError("invalid_path")

    sha256 = nonempty_text(fields["sha256"])
    if re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise CorpusError("invalid_manifest")
    if fields["format"] != expected_format:
        raise CorpusError("invalid_manifest")
    language = nonempty_text(fields["language"])
    if language not in ("fr", "en"):
        raise CorpusError("invalid_manifest")
    author_label = nonempty_text(fields["author_label"], 128)
    subject_label = nonempty_text(fields["subject_label"], 128)
    return (
        fixture_id,
        path,
        sha256,
        cast(Literal["fr", "en"], language),
        author_label,
        subject_label,
    )


def annotation_values(value: object, outcome: str) -> list[object]:
    """Bound reference annotations and prohibit them for nonsuccess outcomes."""
    if not isinstance(value, list) or len(value) > MAX_ANNOTATIONS:
        raise CorpusError("invalid_manifest")
    if outcome != "success" and value:
        raise CorpusError("invalid_manifest")
    return cast(list[object], value)


def manifest_fields(source: bytes, versions: tuple[int, ...]) -> tuple[int, list[object]]:
    """Decode bounded strict JSON and return a validated version and entry list."""
    if len(source) > MAX_MANIFEST_BYTES:
        raise CorpusError("manifest_too_large")
    try:
        parsed: object = json.loads(
            source.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise CorpusError("invalid_manifest") from None

    root = exact_fields(parsed, _ROOT_FIELDS)
    version = root["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version not in versions:
        raise CorpusError("invalid_manifest")
    fixtures = root["fixtures"]
    if not isinstance(fixtures, list) or not 1 <= len(fixtures) <= MAX_FIXTURES:
        raise CorpusError("invalid_manifest")
    return version, cast(list[object], fixtures)


def validate_unique_fixtures(identities: Iterable[tuple[str, str]]) -> None:
    """Reject repeated identifiers or paths across all selected formats."""
    fixture_ids: set[str] = set()
    fixture_paths: set[str] = set()
    for fixture_id, path in identities:
        if fixture_id in fixture_ids or path in fixture_paths:
            raise CorpusError("duplicate_fixture")
        fixture_ids.add(fixture_id)
        fixture_paths.add(path)
