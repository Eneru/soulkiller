"""Parse TXT fixture metadata without reading or decoding a selected source."""

from typing import Literal, cast

from .corpus_error import CorpusError
from .corpus_fixture import CorpusFixture
from .manifest_fields import (
    FIXTURE_FIELDS,
    annotation_values,
    exact_fields,
    nonempty_text,
    nonnegative_integer,
    parse_fixture_metadata,
)
from .text_annotation import TextAnnotation

_ANNOTATION_FIELDS = frozenset(("start", "end", "quote"))


def _annotation(value: object) -> TextAnnotation:
    fields = exact_fields(value, _ANNOTATION_FIELDS)
    start = nonnegative_integer(fields["start"])
    end = nonnegative_integer(fields["end"])
    quote = nonempty_text(fields["quote"])
    if end <= start:
        raise CorpusError("invalid_manifest")
    return TextAnnotation(start, end, quote)


def parse_text_fixture(value: object) -> CorpusFixture:
    """Retain the existing strict TXT shape and codepoint reference spans."""
    fields = exact_fields(value, FIXTURE_FIELDS)
    fixture_id, path, sha256, language, author_label, subject_label = parse_fixture_metadata(
        fields, "txt"
    )
    outcome = nonempty_text(fields["outcome"])
    if outcome not in ("success", "no_text", "invalid_encoding"):
        raise CorpusError("invalid_manifest")
    annotations = annotation_values(fields["annotations"], outcome)
    return CorpusFixture(
        fixture_id=fixture_id,
        path=path,
        sha256=sha256,
        format="txt",
        language=language,
        author_label=author_label,
        subject_label=subject_label,
        outcome=cast(Literal["success", "no_text", "invalid_encoding"], outcome),
        annotations=tuple(_annotation(annotation) for annotation in annotations),
    )
