"""Complete parser-free PDF snapshots and independent deferred expectations."""

import builtins
import os
from dataclasses import FrozenInstanceError
from importlib import import_module, reload
from pathlib import Path
from types import ModuleType

import pytest

from soulkiller_text import confined_files
from soulkiller_text.confined_files import read_confined
from soulkiller_text.corpus_error import CorpusError
from soulkiller_text.load_corpus import load_corpus
from soulkiller_text.pdf_corpus_fixture import PdfCorpusFixture
from soulkiller_text.pdf_fact_annotation import PdfFactAnnotation
from soulkiller_text.synthetic_pdf import build_text_pdf

from .corpus_helpers import fixture_document
from .pdf_corpus_fixtures import (
    ENGLISH_PAGES,
    FRENCH_PAGES,
    PDF_SENTINEL,
    bilingual_corpus,
    pdf_document,
    write_evaluation_corpus,
)


def test_mixed_bilingual_corpus_retains_bytes_labels_and_independent_facts(tmp_path: Path) -> None:
    # Arrange
    bilingual_corpus(tmp_path)
    # Act
    loaded = load_corpus(tmp_path, "corpus")
    # Assert
    assert len(loaded) == 3
    assert loaded[0].source == b"abc"
    assert loaded[1].source == build_text_pdf(FRENCH_PAGES)
    assert loaded[2].source == build_text_pdf(ENGLISH_PAGES)
    assert isinstance(loaded[1].specification, PdfCorpusFixture)
    assert loaded[1].specification.author_label == "  Inez (invented author)  "
    assert loaded[1].specification.subject_label == "Corin (invented subject)"
    assert loaded[1].specification.language == "fr"
    assert loaded[2].specification.language == "en"
    assert loaded[1].specification.annotations == (
        PdfFactAnnotation(2, "Inez garde une lampe bleue."),
    )
    assert loaded[2].specification.annotations == (
        PdfFactAnnotation(1, "Corin collects paper stars."),
    )


@pytest.mark.parametrize("change", ["quote", "count", "outcome"])
def test_loading_does_not_validate_declared_pdf_extraction_expectations(
    tmp_path: Path, change: str
) -> None:
    # Arrange
    source = build_text_pdf(("Only this invented sentence exists.",))
    fixture = pdf_document(source=source)
    fixture.update({"page_count": 1, "annotations": []})
    if change == "quote":
        fixture["annotations"] = [{"page_number": 1, "quote": "This fact is absent."}]
    elif change == "count":
        fixture["page_count"] = 2
    else:
        fixture["outcome"] = "no_text"
    write_evaluation_corpus(tmp_path, [fixture], {"pdfs/archive.pdf": source})
    # Act
    loaded = load_corpus(tmp_path, "corpus")
    # Assert
    assert loaded[0].source == source
    assert isinstance(loaded[0].specification, PdfCorpusFixture)
    if change == "quote":
        assert loaded[0].specification.annotations == (
            PdfFactAnnotation(1, "This fact is absent."),
        )
    elif change == "count":
        assert loaded[0].specification.page_count == 2
    else:
        assert loaded[0].specification.outcome == "no_text"


@pytest.mark.parametrize("outcome", ["success", "no_text", "encrypted_pdf", "malformed_input"])
def test_declared_pdf_format_accepts_hashed_malformed_nonutf8_bytes_regardless_of_extension(
    tmp_path: Path, outcome: str
) -> None:
    # Arrange
    fixture = pdf_document(path="pdfs/actually-named.txt")
    fixture.update({"outcome": outcome, "annotations": []})
    write_evaluation_corpus(tmp_path, [fixture], {"pdfs/actually-named.txt": PDF_SENTINEL})
    # Act
    loaded = load_corpus(tmp_path, "corpus")
    # Assert
    assert loaded[0].source == PDF_SENTINEL
    assert loaded[0].specification.format == "pdf"
    assert loaded[0].specification.outcome == outcome


@pytest.mark.parametrize("invalid", ["type", "aggregate", "fact"])
def test_invalid_later_pdf_metadata_prevents_every_source_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid: str
) -> None:
    # Arrange
    first = fixture_document("first", "first.txt")
    second = pdf_document()
    fixtures = [first, second]
    if invalid == "type":
        second["page_count"] = True
    elif invalid == "aggregate":
        earlier_pdf = pdf_document("earlier-pdf", "pdfs/earlier.pdf")
        earlier_pdf["page_count"] = 19
        fixtures = [first, earlier_pdf, second]
    else:
        second["annotations"] = [{"page_number": 3, "quote": "Outside declared pages."}]
    write_evaluation_corpus(tmp_path, fixtures, {"first.txt": b"abc"})
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


def test_stale_later_pdf_hash_returns_no_partial_mixed_tuple(tmp_path: Path) -> None:
    # Arrange
    first = fixture_document("first", "first.txt")
    second = pdf_document()
    second["sha256"] = "0" * 64
    corpus = write_evaluation_corpus(
        tmp_path, [first, second], {"first.txt": b"abc", "pdfs/archive.pdf": PDF_SENTINEL}
    )
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == "source_mismatch"
    assert (corpus / "first.txt").read_bytes() == b"abc"
    assert (corpus / "pdfs/archive.pdf").read_bytes() == PDF_SENTINEL


def test_public_corpus_import_and_loading_never_import_or_invoke_pdf_parser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    write_evaluation_corpus(tmp_path)
    original_import = builtins.__import__
    attempts: list[str] = []

    def guarded_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> ModuleType:
        if name == "native_pdf" or name.startswith(("pypdf", "soulkiller_text.native_pdf")):
            attempts.append(name)
            raise AssertionError("Corpus loading must not depend on a PDF parser.")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    module = reload(import_module("soulkiller_text.load_corpus"))
    reload(import_module("soulkiller_text"))
    # Act
    loaded = module.load_corpus(tmp_path, "corpus")
    # Assert
    assert loaded[0].source == PDF_SENTINEL
    assert attempts == []


def test_pdf_source_is_read_once_and_returned_as_an_immutable_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    corpus = write_evaluation_corpus(tmp_path)
    module = import_module("soulkiller_text.load_corpus")
    reads: list[str] = []

    def tracked_read(root: int, path: str, maximum: int) -> bytes:
        reads.append(path)
        return read_confined(root, path, maximum)

    monkeypatch.setattr(module, "read_confined", tracked_read)
    # Act
    loaded = load_corpus(tmp_path, "corpus")
    (corpus / "pdfs/archive.pdf").write_bytes(b"An unrelated next revision.")
    # Assert
    assert reads == ["manifest.json", "pdfs/archive.pdf"]
    assert loaded[0].source == PDF_SENTINEL


@pytest.mark.parametrize("field", ["source", "specification"])
def test_loaded_pdf_record_is_frozen(tmp_path: Path, field: str) -> None:
    # Arrange
    write_evaluation_corpus(tmp_path)
    record = load_corpus(tmp_path, "corpus")[0]
    # Act
    with pytest.raises(FrozenInstanceError):
        setattr(record, field, None)
    # Assert
    assert record.source == PDF_SENTINEL


@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo", "hardlink"])
def test_pdf_sources_reject_unsafe_filesystem_objects(tmp_path: Path, kind: str) -> None:
    # Arrange
    corpus = write_evaluation_corpus(tmp_path)
    path = corpus / "pdfs/archive.pdf"
    if kind == "hardlink":
        os.link(path, corpus / "second-link")
    else:
        path.unlink()
        if kind == "symlink":
            outside = tmp_path / "unselected.pdf"
            outside.write_bytes(PDF_SENTINEL)
            path.symlink_to(outside)
        elif kind == "directory":
            path.mkdir()
        else:
            os.mkfifo(path)
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == "unsafe_file"


def test_pdf_source_larger_than_five_mebibytes_fails_without_modifying_it(tmp_path: Path) -> None:
    # Arrange
    source = b"x" * (5 * 1024 * 1024 + 1)
    fixture = pdf_document(source=source)
    corpus = write_evaluation_corpus(tmp_path, [fixture], {"pdfs/archive.pdf": source})
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == "input_too_large"
    assert (corpus / "pdfs/archive.pdf").stat().st_size == len(source)


def test_pdf_source_at_exact_five_mebibyte_boundary_is_verified(tmp_path: Path) -> None:
    # Arrange
    source = b"x" * (5 * 1024 * 1024)
    fixture = pdf_document(source=source)
    write_evaluation_corpus(tmp_path, [fixture], {"pdfs/archive.pdf": source})
    # Act
    loaded = load_corpus(tmp_path, "corpus")
    # Assert
    assert loaded[0].source == source


def test_missing_pdf_source_has_named_failure_without_private_path(tmp_path: Path) -> None:
    # Arrange
    corpus = write_evaluation_corpus(tmp_path)
    (corpus / "pdfs/archive.pdf").unlink()
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == "source_unavailable"
    assert str(failure.value) == "source_unavailable"


@pytest.mark.parametrize("before_acquisition", [True, False])
def test_pdf_replacement_race_never_reads_symlink_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, before_acquisition: bool
) -> None:
    # Arrange
    corpus = write_evaluation_corpus(tmp_path)
    path = corpus / "pdfs/archive.pdf"
    outside = tmp_path / "replacement.pdf"
    outside.write_bytes(b"Never selected replacement.")
    original_open = confined_files._open_leaf

    def replaced_open(parent: int, name: str) -> int:
        if name != "archive.pdf":
            return original_open(parent, name)
        descriptor = None if before_acquisition else original_open(parent, name)
        path.rename(corpus / "pdfs/original.pdf")
        path.symlink_to(outside)
        return original_open(parent, name) if descriptor is None else descriptor

    monkeypatch.setattr(confined_files, "_open_leaf", replaced_open)
    # Act
    if before_acquisition:
        with pytest.raises(CorpusError) as failure:
            load_corpus(tmp_path, "corpus")
    else:
        loaded = load_corpus(tmp_path, "corpus")
    # Assert
    if before_acquisition:
        assert failure.value.category == "unsafe_file"
    else:
        assert loaded[0].source == PDF_SENTINEL
    assert outside.read_bytes() == b"Never selected replacement."
