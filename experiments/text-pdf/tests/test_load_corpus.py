"""Independent complete-corpus selection, expectations and immutable snapshots."""

from dataclasses import FrozenInstanceError
from importlib import import_module
from pathlib import Path

import pytest

from soulkiller_text.confined_files import read_confined
from soulkiller_text.corpus_error import CorpusError
from soulkiller_text.load_corpus import load_corpus

from .corpus_helpers import encode_manifest, fixture_document, manifest_document
from .filesystem_fixtures import DEFAULT_SOURCE, SOURCE_PATH, write_corpus


def test_selected_unicode_corpus_preserves_bytes_labels_and_codepoint_annotations(
    tmp_path: Path,
) -> None:
    # Arrange
    corpus = write_corpus(
        tmp_path,
        changes={"annotations": [{"start": 1, "end": 6, "quote": "é e\u0301🌟"}]},
    )
    (corpus / "unlisted.txt").write_bytes(b"This file must not be selected.")
    # Act
    loaded = load_corpus(tmp_path, "corpus")
    # Assert
    assert len(loaded) == 1
    assert loaded[0].source == DEFAULT_SOURCE
    assert loaded[0].specification.path == SOURCE_PATH
    assert loaded[0].specification.author_label == "Inez (invented author)"
    assert loaded[0].specification.subject_label == "Corin (invented subject)"
    assert loaded[0].specification.annotations[0].quote == "é e\u0301🌟"


@pytest.mark.parametrize("source,outcome", [(b"", "no_text"), (b"\xff", "invalid_encoding")])
def test_explicit_empty_or_invalid_encoding_expectations_are_valid(
    tmp_path: Path, source: bytes, outcome: str
) -> None:
    # Arrange
    write_corpus(tmp_path, source, {"outcome": outcome})
    # Act
    loaded = load_corpus(tmp_path, "corpus")
    # Assert
    assert loaded[0].source == source
    assert loaded[0].specification.outcome == outcome


@pytest.mark.parametrize(
    "changes,category",
    [
        ({"sha256": "0" * 64}, "source_mismatch"),
        ({"outcome": "no_text"}, "expectation_mismatch"),
        ({"annotations": [{"start": 0, "end": 1, "quote": "B"}]}, "expectation_mismatch"),
        ({"annotations": [{"start": 0, "end": 100, "quote": "A"}]}, "expectation_mismatch"),
    ],
    ids=["stale-revision", "wrong-outcome", "wrong-quote", "span-past-source"],
)
def test_stale_source_or_expectations_never_return_a_partial_corpus(
    tmp_path: Path, changes: dict[str, object], category: str
) -> None:
    # Arrange
    write_corpus(tmp_path, changes=changes)
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == category
    assert "Inez" not in str(failure.value)
    assert str(tmp_path) not in str(failure.value)


def test_missing_selected_source_has_a_named_failure(tmp_path: Path) -> None:
    # Arrange
    corpus = write_corpus(tmp_path)
    (corpus / SOURCE_PATH).unlink()
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == "source_unavailable"


def test_invalid_schema_prevents_all_fixture_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    corpus = write_corpus(tmp_path)
    (corpus / "manifest.json").write_text('{"schema_version":1,"fixtures":[],"extra":0}')
    reads: list[str] = []
    module = import_module("soulkiller_text.load_corpus")

    def tracked_read(root: int, path: str, maximum: int) -> bytes:
        reads.append(path)
        return read_confined(root, path, maximum)

    monkeypatch.setattr(module, "read_confined", tracked_read)
    # Act
    with pytest.raises(CorpusError):
        load_corpus(tmp_path, "corpus")
    # Assert
    assert reads == ["manifest.json"]


def test_loaded_snapshot_remains_unchanged_after_source_replacement(tmp_path: Path) -> None:
    # Arrange
    corpus = write_corpus(tmp_path)
    loaded = load_corpus(tmp_path, "corpus")
    # Act
    (corpus / SOURCE_PATH).write_bytes(b"A new revision.")
    # Assert
    assert loaded[0].source == DEFAULT_SOURCE


@pytest.mark.parametrize("field", ["specification", "source"])
def test_loaded_records_are_immutable(tmp_path: Path, field: str) -> None:
    # Arrange
    write_corpus(tmp_path)
    record = load_corpus(tmp_path, "corpus")[0]
    # Act
    with pytest.raises(FrozenInstanceError):
        setattr(record, field, None)
    # Assert
    assert record.source == DEFAULT_SOURCE


def test_hand_authored_repository_corpus_is_consistent() -> None:
    # Arrange
    workspace = Path(__file__).absolute().parents[3]
    # Act
    loaded = load_corpus(workspace, "experiments/text-pdf/corpus")
    # Assert
    assert len(loaded) == 5
    assert {record.specification.language for record in loaded} == {"fr", "en"}
    assert {record.specification.outcome for record in loaded} == {
        "success",
        "no_text",
        "invalid_encoding",
    }


def test_oversized_manifest_fails_before_json_or_fixture_processing(tmp_path: Path) -> None:
    # Arrange
    corpus = write_corpus(tmp_path)
    (corpus / "manifest.json").write_bytes(b" " * (128 * 1024 + 1))
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == "manifest_too_large"
    assert (corpus / SOURCE_PATH).read_bytes() == DEFAULT_SOURCE


def test_invalid_later_fixture_prevents_even_valid_first_source_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    corpus = write_corpus(tmp_path, b"abc")
    first = fixture_document("first", SOURCE_PATH)
    second = fixture_document("second", "nested/second.txt")
    second["format"] = "pdf"
    (corpus / "manifest.json").write_bytes(encode_manifest(manifest_document([first, second])))
    module = import_module("soulkiller_text.load_corpus")
    reads: list[str] = []

    def tracked_read(root: int, path: str, maximum: int) -> bytes:
        reads.append(path)
        return read_confined(root, path, maximum)

    monkeypatch.setattr(module, "read_confined", tracked_read)
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == "invalid_manifest"
    assert reads == ["manifest.json"]


def test_stale_later_revision_does_not_return_earlier_valid_snapshot(tmp_path: Path) -> None:
    # Arrange
    corpus = write_corpus(tmp_path, b"abc")
    first = fixture_document("first", SOURCE_PATH)
    second = fixture_document("second", "nested/second.txt")
    second["sha256"] = "0" * 64
    (corpus / "nested/second.txt").write_bytes(b"abc")
    (corpus / "manifest.json").write_bytes(encode_manifest(manifest_document([first, second])))
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == "source_mismatch"
    assert (corpus / SOURCE_PATH).read_bytes() == b"abc"
    assert (corpus / "nested/second.txt").read_bytes() == b"abc"
