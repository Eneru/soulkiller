"""A pure version-1 codec for one supervised fixture row, not a comparison report."""

from . import fixture_record_constants as constants
from .corpus_fixture import CorpusFixture
from .fixture_record_error import FixtureRecordError
from .fixture_record_fields import decode_fields, encode_fields, validate_specification
from .fixture_record_result import decode_nested_result, result_fields
from .fixture_run import FixtureRun
from .pdf_corpus_fixture import PdfCorpusFixture
from .run_status import RunStatus


def _observations(
    fields: dict[str, object], *, completed: bool
) -> tuple[int | None, RunStatus | None]:
    """Keep observed counts distinct from unknown interrupted and never-started observations."""
    count = fields["output_bytes"]
    reason = fields["unfinished_reason"]
    if count is not None and (
        type(count) is not int or not 0 <= count <= constants.MAX_OBSERVED_OUTPUT_BYTES
    ):
        raise FixtureRecordError(constants.INVALID_RECORD)
    if completed:
        if type(count) is not int or reason is not None:
            raise FixtureRecordError(constants.INVALID_RECORD)
        return count, None
    if type(reason) is not str:
        raise FixtureRecordError(constants.INVALID_RECORD)
    try:
        status = RunStatus(reason)
    except ValueError:
        raise FixtureRecordError(constants.INVALID_RECORD) from None
    if status is RunStatus.COMPLETE or (
        count != 0
        and not (count is None and status in (RunStatus.CANCELLED, RunStatus.CLEANUP_FAILURE))
    ):
        raise FixtureRecordError(constants.INVALID_RECORD)
    return count, status


def _decode_row(
    fields: dict[str, object], specification: CorpusFixture | PdfCorpusFixture
) -> FixtureRun:
    """Bind the declared version and source identity before restoring typed observations."""
    if (
        type(fields["schema_version"]) is not int
        or fields["schema_version"] != constants.SCHEMA_VERSION
        or type(fields["fixture_id"]) is not str
        or fields["fixture_id"] != specification.fixture_id
        or type(fields["format"]) is not str
        or fields["format"] != specification.format
        or type(fields["source_sha256"]) is not str
        or fields["source_sha256"] != specification.sha256
    ):
        raise FixtureRecordError(constants.INVALID_RECORD)
    result = decode_nested_result(fields["result"], specification)
    count, reason = _observations(fields, completed=result is not None)
    return FixtureRun(specification, result, count, reason)


def encode_fixture_record(row: FixtureRun) -> bytes:
    """Validate one exact immutable row and encode bounded JSON without normalizing evidence."""
    try:
        if type(row) is not FixtureRun:
            raise FixtureRecordError(constants.INVALID_RECORD)
        validate_specification(row.specification)
        if row.unfinished_reason is not None and type(row.unfinished_reason) is not RunStatus:
            raise FixtureRecordError(constants.INVALID_RECORD)
        fields: dict[str, object] = {
            "schema_version": constants.SCHEMA_VERSION,
            "fixture_id": row.specification.fixture_id,
            "format": row.specification.format,
            "source_sha256": row.specification.sha256,
            "result": result_fields(row.result, row.specification),
            "output_bytes": row.output_bytes,
            "unfinished_reason": (
                row.unfinished_reason.value if row.unfinished_reason is not None else None
            ),
        }
        _decode_row(fields, row.specification)
        return encode_fields(fields)
    except AttributeError:
        raise FixtureRecordError(constants.INVALID_RECORD) from None


def decode_fixture_record(
    payload: bytes, specification: CorpusFixture | PdfCorpusFixture
) -> FixtureRun:
    """Restore one strict revision-bound row using caller-accepted metadata without source I/O."""
    try:
        validate_specification(specification)
        return _decode_row(decode_fields(payload), specification)
    except AttributeError:
        raise FixtureRecordError(constants.INVALID_RECORD) from None
