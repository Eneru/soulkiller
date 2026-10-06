"""Validate bounded synthetic TXT manifests before any source-file access."""

import json
import re
from typing import Literal, Never, cast

from .corpus_constants import MAX_ANNOTATIONS, MAX_FIXTURES, MAX_MANIFEST_BYTES
from .corpus_error import CorpusError
from .corpus_fixture import CorpusFixture
from .corpus_paths import validate_relative_path
from .text_annotation import TextAnnotation

_ROOT_FIELDS = frozenset(("schema_version", "fixtures"))
_FIXTURE_FIELDS = frozenset(
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
_ANNOTATION_FIELDS = frozenset(("start", "end", "quote"))


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CorpusError("invalid_manifest")
        result[key] = value
    return result


def _reject_constant(value: str) -> Never:
    raise CorpusError("invalid_manifest")


def _fields(value: object, expected: frozenset[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise CorpusError("invalid_manifest")
    return cast(dict[str, object], value)


def _text(value: object, maximum: int | None = None) -> str:
    if (
        not isinstance(value, str)
        or not value
        or (maximum is not None and len(value) > maximum)
        or any(0xD800 <= ord(character) <= 0xDFFF for character in value)
    ):
        raise CorpusError("invalid_manifest")
    return value


def _offset(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CorpusError("invalid_manifest")
    return value


def _annotation(value: object) -> TextAnnotation:
    fields = _fields(value, _ANNOTATION_FIELDS)
    start = _offset(fields["start"])
    end = _offset(fields["end"])
    quote = _text(fields["quote"])
    if end <= start:
        raise CorpusError("invalid_manifest")
    return TextAnnotation(start, end, quote)


def _fixture(value: object) -> CorpusFixture:
    fields = _fields(value, _FIXTURE_FIELDS)
    fixture_id = _text(fields["id"])
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", fixture_id) is None:
        raise CorpusError("invalid_manifest")

    path = fields["path"]
    if not isinstance(path, str):
        raise CorpusError("invalid_path")
    validate_relative_path(path)
    if path == "manifest.json":
        raise CorpusError("invalid_path")

    sha256 = _text(fields["sha256"])
    if re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise CorpusError("invalid_manifest")
    if fields["format"] != "txt":
        raise CorpusError("invalid_manifest")
    language = _text(fields["language"])
    if language not in ("fr", "en"):
        raise CorpusError("invalid_manifest")
    author_label = _text(fields["author_label"], 128)
    subject_label = _text(fields["subject_label"], 128)
    outcome = _text(fields["outcome"])
    if outcome not in ("success", "no_text", "invalid_encoding"):
        raise CorpusError("invalid_manifest")

    annotations = fields["annotations"]
    if not isinstance(annotations, list) or len(annotations) > MAX_ANNOTATIONS:
        raise CorpusError("invalid_manifest")
    parsed_annotations = tuple(_annotation(annotation) for annotation in annotations)
    if outcome != "success" and parsed_annotations:
        raise CorpusError("invalid_manifest")

    return CorpusFixture(
        fixture_id=fixture_id,
        path=path,
        sha256=sha256,
        format="txt",
        language=cast(Literal["fr", "en"], language),
        author_label=author_label,
        subject_label=subject_label,
        outcome=cast(Literal["success", "no_text", "invalid_encoding"], outcome),
        annotations=parsed_annotations,
    )


def parse_manifest(source: bytes) -> tuple[CorpusFixture, ...]:
    """Validate schema version 1, returning immutable metadata without I/O.

    CorpusError categories are manifest_too_large, invalid_manifest,
    invalid_path and duplicate_fixture. Messages never include input data.
    """
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

    root = _fields(parsed, _ROOT_FIELDS)
    version = root["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version != 1:
        raise CorpusError("invalid_manifest")
    fixtures = root["fixtures"]
    if not isinstance(fixtures, list) or not 1 <= len(fixtures) <= MAX_FIXTURES:
        raise CorpusError("invalid_manifest")

    result = tuple(_fixture(fixture) for fixture in fixtures)
    fixture_ids: set[str] = set()
    fixture_paths: set[str] = set()
    for fixture in result:
        if fixture.fixture_id in fixture_ids or fixture.path in fixture_paths:
            raise CorpusError("duplicate_fixture")
        fixture_ids.add(fixture.fixture_id)
        fixture_paths.add(fixture.path)
    return result
