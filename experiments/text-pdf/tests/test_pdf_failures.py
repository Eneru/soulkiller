"""Boundary doubles for visible PDF failures and future supervision propagation."""

import builtins
import logging
from collections.abc import Mapping, Sequence
from io import BytesIO
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, Mock

import pypdf
import pytest
from pypdf.errors import DependencyError, PdfReadError

from soulkiller_text.native_pdf import extract_native_pdf
from soulkiller_text.pdf_outcome import PdfOutcome
from soulkiller_text.synthetic_pdf import build_text_pdf

from .pdf_fixtures import page_double, reader_double


@pytest.mark.parametrize(
    ("failure", "outcome"),
    [
        (PdfReadError("private fixture details"), PdfOutcome.MALFORMED_INPUT),
        (DependencyError("private fixture details"), PdfOutcome.UNSUPPORTED_DEPENDENCY),
        (ImportError("private fixture details"), PdfOutcome.UNSUPPORTED_DEPENDENCY),
        (RuntimeError("private fixture details"), PdfOutcome.CANDIDATE_FAILURE),
    ],
)
def test_reader_failure_has_safe_explicit_outcome(
    monkeypatch: pytest.MonkeyPatch, failure: Exception, outcome: PdfOutcome
) -> None:
    # Arrange
    source = build_text_pdf(("Invented text.",))
    monkeypatch.setattr(pypdf, "PdfReader", Mock(side_effect=failure))
    # Act
    result = extract_native_pdf(source)
    # Assert
    assert result.outcome is outcome
    assert result.pages == ()
    assert result.total_pages is None
    assert result.missing_pages == ()
    assert "private fixture details" not in repr(result)


@pytest.mark.parametrize(
    ("failure", "outcome"),
    [
        (PdfReadError("private page tree"), PdfOutcome.MALFORMED_INPUT),
        (DependencyError("private page tree"), PdfOutcome.UNSUPPORTED_DEPENDENCY),
        (RuntimeError("private page tree"), PdfOutcome.CANDIDATE_FAILURE),
    ],
)
def test_page_count_failure_has_safe_explicit_outcome(
    monkeypatch: pytest.MonkeyPatch, failure: Exception, outcome: PdfOutcome
) -> None:
    # Arrange
    pages = MagicMock()
    pages.__len__.side_effect = failure
    reader = SimpleNamespace(is_encrypted=False, pages=pages)
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader))
    # Act
    result = extract_native_pdf(build_text_pdf(("Invented text.",)))
    # Assert
    assert result.outcome is outcome
    assert result.pages == ()
    assert result.total_pages is None
    assert result.missing_pages == ()


def test_one_failed_page_preserves_later_physical_page(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    failed = page_double(error=PdfReadError("private failure"))
    successful = page_double("Independent page two.")
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader_double(failed, successful)))
    # Act
    result = extract_native_pdf(build_text_pdf(("First.", "Second.")))
    # Assert
    assert result.outcome is PdfOutcome.PARTIAL
    assert result.total_pages == 2
    assert result.missing_pages == (1,)
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 2
    assert result.pages[0].text == "Independent page two."


def test_empty_covered_page_with_failure_is_partial(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    reader = reader_double(page_double(""), page_double(error=RuntimeError("private failure")))
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader))
    # Act
    result = extract_native_pdf(build_text_pdf(("", "Second.")))
    # Assert
    assert result.outcome is PdfOutcome.PARTIAL
    assert result.total_pages == 2
    assert result.missing_pages == (2,)
    assert result.pages[0].page_number == 1
    assert result.pages[0].text == ""


def test_all_failed_pages_are_candidate_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    reader = reader_double(
        page_double(error=RuntimeError("first private failure")),
        page_double(error=PdfReadError("second private failure")),
    )
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader))
    # Act
    result = extract_native_pdf(build_text_pdf(("First.", "Second.")))
    # Assert
    assert result.outcome is PdfOutcome.CANDIDATE_FAILURE
    assert result.total_pages == 2
    assert result.missing_pages == (1, 2)
    assert result.pages == ()


@pytest.mark.parametrize("text", [42, b"wrong type"], ids=["integer", "bytes"])
def test_invalid_candidate_page_text_is_not_promoted_to_success(
    monkeypatch: pytest.MonkeyPatch, text: object
) -> None:
    # Arrange
    reader = reader_double(page_double(text))
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader))
    # Act
    result = extract_native_pdf(build_text_pdf(("Independent text.",)))
    # Assert
    assert result.outcome is PdfOutcome.CANDIDATE_FAILURE
    assert result.pages == ()
    assert result.missing_pages == (1,)


def test_none_candidate_text_is_retained_as_empty_page(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    reader = reader_double(page_double(None))
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader))
    # Act
    result = extract_native_pdf(build_text_pdf(("",)))
    # Assert
    assert result.outcome is PdfOutcome.NO_TEXT
    assert result.total_pages == 1
    assert result.pages[0].text == ""
    assert result.missing_pages == ()


@pytest.mark.parametrize("stage", ["reader", "page-count", "page-text"])
@pytest.mark.parametrize("failure_type", [MemoryError, KeyboardInterrupt])
def test_resource_and_cancellation_errors_propagate_for_external_supervision(
    monkeypatch: pytest.MonkeyPatch, stage: str, failure_type: type[BaseException]
) -> None:
    # Arrange
    failure = failure_type()
    parser = Mock()
    if stage == "reader":
        parser.side_effect = failure
    elif stage == "page-count":
        pages = MagicMock()
        pages.__len__.side_effect = failure
        parser.return_value = SimpleNamespace(is_encrypted=False, pages=pages)
    else:
        parser.return_value = reader_double(page_double(error=failure))
    monkeypatch.setattr(pypdf, "PdfReader", parser)
    # Act / Assert
    with pytest.raises(failure_type):
        extract_native_pdf(build_text_pdf(("Independent text.",)))


def test_page_ceiling_stops_before_any_page_extraction(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    pages = [page_double("Do not extract.") for _ in range(3)]
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader_double(*pages)))
    # Act
    result = extract_native_pdf(build_text_pdf(("One.", "Two.", "Three.")), max_pages=2)
    # Assert
    assert result.outcome is PdfOutcome.PAGE_LIMIT
    assert result.total_pages == 3
    assert result.pages == ()
    assert result.missing_pages == ()
    for page in pages:
        page.extract_text.assert_not_called()


def test_protected_reader_stops_before_page_count(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    pages = MagicMock()
    pages.__len__.side_effect = AssertionError("must not inspect protected pages")
    reader = SimpleNamespace(is_encrypted=True, pages=pages)
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader))
    # Act
    result = extract_native_pdf(build_text_pdf(("Invented text.",)))
    # Assert
    assert result.outcome is PdfOutcome.ENCRYPTED_PDF
    assert result.pages == ()
    pages.__len__.assert_not_called()


def test_external_helper_configuration_precedes_reader(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    events: list[tuple[str, object]] = []
    source = build_text_pdf(("Independent text.",))
    reader = reader_double(page_double("Independent text."))

    def configure(**kwargs: object) -> None:
        events.append(("configuration", kwargs))

    def create_reader(stream: BytesIO, **kwargs: object) -> SimpleNamespace:
        events.append(("reader", (stream.getvalue(), kwargs)))
        return reader

    monkeypatch.setattr(pypdf, "overwrite_configuration", configure)
    monkeypatch.setattr(pypdf, "PdfReader", create_reader)
    # Act
    result = extract_native_pdf(source)
    # Assert
    assert result.outcome is PdfOutcome.SUCCESS
    assert events == [
        ("configuration", {"jbig2dec_binary": None, "disable_legacy_handling": True}),
        ("reader", (source, {"strict": False, "password": None})),
    ]


def test_page_text_is_unchanged_and_plain_mode_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    independent_text = "  e\u0301\r\nInvented second line.  "
    page = page_double(independent_text)
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader_double(page)))
    # Act
    result = extract_native_pdf(build_text_pdf(("Independent source.",)))
    # Assert
    assert result.outcome is PdfOutcome.SUCCESS
    assert result.pages[0].text == independent_text
    page.extract_text.assert_called_once_with(extraction_mode="plain")


def test_missing_parser_module_is_explicit_dependency_blocker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    original_import = builtins.__import__

    def without_parser(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> ModuleType:
        if name == "pypdf.errors":
            raise ImportError("private installation details")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", without_parser)
    # Act
    result = extract_native_pdf(build_text_pdf(("Independent text.",)))
    # Assert
    assert result.outcome is PdfOutcome.UNSUPPORTED_DEPENDENCY
    assert result.pages == ()


def test_parser_warning_and_failure_do_not_emit_sensitive_diagnostics(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    def failing_reader(*arguments: object, **kwargs: object) -> object:
        logging.getLogger("pypdf._reader").warning("private fixture diagnostics")
        raise PdfReadError("private fixture diagnostics")

    monkeypatch.setattr(pypdf, "PdfReader", failing_reader)
    # Act
    result = extract_native_pdf(build_text_pdf(("Independent text.",)))
    output = capsys.readouterr()
    # Assert
    assert result.outcome is PdfOutcome.MALFORMED_INPUT
    assert output.out == ""
    assert output.err == ""
    assert "private fixture diagnostics" not in repr(result)


def test_zero_page_reader_retains_known_empty_document(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader_double()))
    # Act
    result = extract_native_pdf(build_text_pdf(("Independent source.",)))
    # Assert
    assert result.outcome is PdfOutcome.NO_TEXT
    assert result.total_pages == 0
    assert result.pages == ()
    assert result.missing_pages == ()


def test_exact_byte_limit_is_accepted_before_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    source = b"x" * (5 * 1024 * 1024)
    parser = Mock(return_value=reader_double(page_double("Independent text.")))
    monkeypatch.setattr(pypdf, "PdfReader", parser)
    # Act
    result = extract_native_pdf(source)
    # Assert
    assert result.outcome is PdfOutcome.SUCCESS
    parser.assert_called_once()


def test_huge_reported_page_count_is_rejected_without_missing_page_allocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    pages = MagicMock()
    pages.__len__.return_value = 10**9
    reader = SimpleNamespace(is_encrypted=False, pages=pages)
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader))
    # Act
    result = extract_native_pdf(build_text_pdf(("Independent source.",)))
    # Assert
    assert result.outcome is PdfOutcome.PAGE_LIMIT
    assert result.total_pages == 10**9
    assert result.pages == ()
    assert result.missing_pages == ()
    pages.__getitem__.assert_not_called()


@pytest.mark.parametrize(
    ("failure_type", "outcome"),
    [
        (DependencyError, PdfOutcome.UNSUPPORTED_DEPENDENCY),
        (PdfReadError, PdfOutcome.MALFORMED_INPUT),
        (RuntimeError, PdfOutcome.CANDIDATE_FAILURE),
    ],
)
def test_uniform_page_failures_preserve_explicit_failure_category(
    monkeypatch: pytest.MonkeyPatch, failure_type: type[Exception], outcome: PdfOutcome
) -> None:
    # Arrange
    reader = reader_double(
        page_double(error=failure_type("first private details")),
        page_double(error=failure_type("second private details")),
    )
    monkeypatch.setattr(pypdf, "PdfReader", Mock(return_value=reader))
    # Act
    result = extract_native_pdf(build_text_pdf(("First.", "Second.")))
    # Assert
    assert result.outcome is outcome
    assert result.total_pages == 2
    assert result.pages == ()
    assert result.missing_pages == (1, 2)
