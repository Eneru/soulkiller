"""Typed rows compose explicitly with real create-only confined storage."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from soulkiller_text.fixture_record import decode_fixture_record, encode_fixture_record
from soulkiller_text.fixture_record_error import FixtureRecordError
from soulkiller_text.fixture_run import FixtureRun
from soulkiller_text.pdf_worker import run_observed_pdf_worker
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.run_store import create_run_store, open_run_store
from soulkiller_text.run_store_error import RunStoreError
from soulkiller_text.run_text_worker import run_observed_text_worker
from soulkiller_text.synthetic_pdf import build_text_pdf
from soulkiller_text.worker_outcome import WorkerOutcome

from .fixture_record_fixtures import (
    pdf_row,
    source_specification,
    text_document,
    text_row,
    wire,
)
from .pdf_worker_fixtures import externally_offline
from .run_store_fixtures import RUN_ID, directory_entries, run_directory, workspace_with_source
from .synthetic_sources import BILINGUAL_BYTES, BILINGUAL_TEXT


def test_real_store_reopens_an_exact_typed_row_after_handle_closure(tmp_path: Path) -> None:
    """The filesystem frame remains opaque while a later codec restores the same row."""
    # Arrange
    workspace = workspace_with_source(tmp_path)
    row = pdf_row()
    payload = encode_fixture_record(row)
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("fixture-pdf", payload)
    # Act
    with open_run_store(workspace, "corpus", RUN_ID) as reopened:
        restored = decode_fixture_record(reopened.read_record("fixture-pdf"), row.specification)
    # Assert
    assert restored == row
    assert restored.specification is row.specification
    assert directory_entries(run_directory(workspace)) == {"fixture-pdf"}


def test_codec_payload_does_not_bypass_existing_record_protection(tmp_path: Path) -> None:
    """A later attempt cannot replace an already published fixture record."""
    # Arrange
    workspace = workspace_with_source(tmp_path)
    row = text_row()
    original = encode_fixture_record(row)
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("fixture-text", original)
        # Act
        with pytest.raises(RunStoreError) as failure:
            store.write_record("fixture-text", encode_fixture_record(pdf_row()))
        # Assert
        assert failure.value.category == "record_exists"
        assert store.read_record("fixture-text") == original


def test_invalid_typed_observation_creates_no_record_or_scratch(tmp_path: Path) -> None:
    """Validation fails before any optional caller publication touches the filesystem."""
    # Arrange
    workspace = workspace_with_source(tmp_path)
    row = replace(text_row(), result=None)
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        # Act
        with pytest.raises(FixtureRecordError):
            store.write_record("fixture-text", encode_fixture_record(row))
    # Assert
    assert directory_entries(run_directory(workspace)) == set()


def test_complete_storage_frame_does_not_establish_valid_json_evidence(tmp_path: Path) -> None:
    """Integrity framing cannot promote semantically forged observations into accepted rows."""
    # Arrange
    workspace = workspace_with_source(tmp_path)
    document = text_document()
    document["output_bytes"] = True
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("forged-row", wire(document))
        intact_payload = store.read_record("forged-row")
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(intact_payload, text_row().specification)
    # Assert
    assert json.loads(intact_payload)["output_bytes"] is True


def test_real_text_worker_observation_persists_without_modifying_runner(tmp_path: Path) -> None:
    """A real guarded TXT subprocess feeds the explicit codec/store composition."""
    # Arrange
    workspace = workspace_with_source(tmp_path)
    specification = source_specification(BILINGUAL_BYTES, "txt")
    execution = run_observed_text_worker(BILINGUAL_BYTES)
    row = FixtureRun(specification, execution.result, execution.output_bytes)
    # Act
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("text-worker", encode_fixture_record(row))
    with open_run_store(workspace, "corpus", RUN_ID) as store:
        restored = decode_fixture_record(store.read_record("text-worker"), specification)
    # Assert
    assert restored == row
    assert execution.result.outcome is WorkerOutcome.SUCCESS
    assert execution.result.text == BILINGUAL_TEXT
    assert execution.output_bytes > 0


def test_real_pdf_worker_observation_persists_under_supplied_network_boundary(
    tmp_path: Path,
) -> None:
    """The offline lane proves native PDF output; the connected lane preserves early refusal."""
    # Arrange
    workspace = workspace_with_source(tmp_path)
    source = build_text_pdf(("Une mémoire inventée.", "An independent invented fact."))
    specification = source_specification(source, "pdf")
    offline = externally_offline()
    execution = run_observed_pdf_worker(source, max_pages=2)
    row = FixtureRun(specification, execution.result, execution.output_bytes)
    # Act
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("pdf-worker", encode_fixture_record(row))
    with open_run_store(workspace, "corpus", RUN_ID) as store:
        restored = decode_fixture_record(store.read_record("pdf-worker"), specification)
    # Assert
    assert restored == row
    expected = PdfWorkerOutcome.SUCCESS if offline else PdfWorkerOutcome.UNSUPPORTED_ENVIRONMENT
    assert execution.result.outcome is expected
    assert execution.result.total_pages == (2 if offline else None)
    assert execution.output_bytes > 0 if offline else execution.output_bytes == 0
