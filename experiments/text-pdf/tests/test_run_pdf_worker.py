"""Real PDF subprocess outcomes depend explicitly on the supplied network namespace."""

import hashlib
import importlib
from typing import cast

import pytest

from soulkiller_text.pdf_worker import run_pdf_worker
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.synthetic_pdf import build_image_pdf, build_text_pdf
from soulkiller_text.worker_limits import WorkerLimits

from .pdf_fixtures import (
    ENGLISH_FACT_PAGES,
    ENGLISH_PAGES,
    FRENCH_FACT_PAGES,
    FRENCH_PAGES,
    MALFORMED_PDF_SOURCES,
    protected_pdf,
)
from .pdf_worker_fixtures import empty_pdf, externally_offline
from .worker_process_helpers import assert_reaped, record_processes


@pytest.mark.parametrize(
    ("pages", "facts"),
    [(FRENCH_PAGES, FRENCH_FACT_PAGES), (ENGLISH_PAGES, ENGLISH_FACT_PAGES)],
    ids=["french", "english"],
)
def test_real_pdf_preserves_independent_facts_only_in_offline_container(
    pages: tuple[str, ...],
    facts: tuple[tuple[str, int], ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    source = build_text_pdf(pages)
    expected_hash = hashlib.sha256(source).hexdigest()
    offline = externally_offline()
    processes = record_processes(monkeypatch)
    # Act
    result = run_pdf_worker(source)
    # Assert
    assert result.source_sha256 == expected_hash
    assert_reaped(processes)
    if offline:
        assert result.outcome is PdfWorkerOutcome.SUCCESS
        assert result.total_pages == 2
        assert result.missing_pages == ()
        assert tuple(page.text for page in result.pages) == pages
        for fact, physical_page in facts:
            assert fact in result.pages[physical_page - 1].text
    else:
        assert result.outcome is PdfWorkerOutcome.UNSUPPORTED_ENVIRONMENT
        assert result.pages == ()
        assert result.total_pages is None
        assert result.missing_pages == ()


@pytest.mark.parametrize(
    "source",
    [build_text_pdf(("",)), build_text_pdf(("  ",)), build_image_pdf(), empty_pdf()],
    ids=["blank", "whitespace", "image-only", "zero-pages"],
)
def test_real_pdf_no_text_retains_physical_coverage_only_offline(source: bytes) -> None:
    # Arrange
    offline = externally_offline()
    # Act
    result = run_pdf_worker(source)
    # Assert
    assert result.outcome == ("no_text" if offline else "unsupported_environment")
    assert result.source_sha256 == hashlib.sha256(source).hexdigest()
    assert result.missing_pages == ()
    if offline:
        assert result.total_pages == len(result.pages)
        assert not any(page.text.strip() for page in result.pages)
    else:
        assert result.total_pages is None
        assert result.pages == ()


@pytest.mark.parametrize("password", ["invented-protection", ""])
def test_real_protected_pdf_is_not_decrypted_or_attributed(password: str) -> None:
    # Arrange
    source = protected_pdf(build_text_pdf(("Invented private fact.",)), password)
    offline = externally_offline()
    # Act
    result = run_pdf_worker(source)
    # Assert
    assert result.outcome == ("encrypted_pdf" if offline else "unsupported_environment")
    assert result.source_sha256 == hashlib.sha256(source).hexdigest()
    assert result.total_pages is None
    assert result.pages == ()
    assert result.missing_pages == ()


@pytest.mark.parametrize("source", MALFORMED_PDF_SOURCES)
def test_real_malformed_pdf_has_no_page_evidence_or_raw_diagnostics(source: bytes) -> None:
    # Arrange
    offline = externally_offline()
    # Act
    result = run_pdf_worker(source)
    # Assert
    assert result.outcome == ("malformed_input" if offline else "unsupported_environment")
    assert result.source_sha256 == hashlib.sha256(source).hexdigest()
    assert result.total_pages is None
    assert result.pages == ()
    assert result.missing_pages == ()


@pytest.mark.parametrize(("count", "ceiling"), [(21, 20), (3, 2)])
def test_real_pdf_page_ceiling_does_not_expand_missing_page_records(
    count: int, ceiling: int
) -> None:
    # Arrange
    source = build_text_pdf(tuple("Invented fact." for _ in range(count)))
    offline = externally_offline()
    # Act
    result = run_pdf_worker(source, max_pages=ceiling)
    # Assert
    assert result.outcome == ("page_limit" if offline else "unsupported_environment")
    assert result.total_pages == (count if offline else None)
    assert result.pages == ()
    assert result.missing_pages == ()


def test_exact_twenty_page_bound_runs_real_native_pdf_offline() -> None:
    # Arrange
    pages = tuple(f"Independent fact {number}." for number in range(1, 21))
    source = build_text_pdf(pages)
    offline = externally_offline()
    # Act
    result = run_pdf_worker(source)
    # Assert
    assert result.outcome == ("success" if offline else "unsupported_environment")
    if offline:
        assert tuple(page.page_number for page in result.pages) == tuple(range(1, 21))
        assert tuple(page.text for page in result.pages) == pages
    else:
        assert result.pages == ()


@pytest.mark.parametrize("ceiling", [True, 0, -1, 21, 1.0, None, "2"])
def test_invalid_public_page_bound_prevents_launch(
    ceiling: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    entry = importlib.import_module("soulkiller_text.pdf_worker")
    launched: list[object] = []
    monkeypatch.setattr(entry, "run_command", lambda *args: launched.append(args))
    # Act
    with pytest.raises(ValueError, match="invalid_pdf_page_limit"):
        run_pdf_worker(b"synthetic", max_pages=cast(int, ceiling))
    # Assert
    assert launched == []


@pytest.mark.parametrize("source", [bytearray(b"pdf"), memoryview(b"pdf"), "pdf", None])
def test_invalid_public_source_prevents_launch(
    source: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    entry = importlib.import_module("soulkiller_text.pdf_worker")
    launched: list[object] = []
    monkeypatch.setattr(entry, "run_command", lambda *args: launched.append(args))
    # Act
    with pytest.raises(TypeError, match="invalid_worker_source"):
        run_pdf_worker(cast(bytes, source))
    # Assert
    assert launched == []


def test_oversized_pdf_source_prevents_launch(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    entry = importlib.import_module("soulkiller_text.pdf_worker")
    launched: list[object] = []
    monkeypatch.setattr(entry, "run_command", lambda *args: launched.append(args))
    # Act
    with pytest.raises(ValueError, match="worker_input_too_large"):
        run_pdf_worker(b"x" * (5 * 1024**2 + 1))
    # Assert
    assert launched == []


def test_invalid_public_resource_profile_prevents_launch(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    entry = importlib.import_module("soulkiller_text.pdf_worker")
    launched: list[object] = []
    monkeypatch.setattr(entry, "run_command", lambda *args: launched.append(args))
    # Act
    with pytest.raises(ValueError, match="invalid_worker_limits"):
        run_pdf_worker(b"synthetic", cast(WorkerLimits, object()))
    # Assert
    assert launched == []


def test_nonlinux_environment_returns_safe_unsupported_without_launch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    entry = importlib.import_module("soulkiller_text.pdf_worker")
    launched: list[object] = []
    monkeypatch.setattr(entry.sys, "platform", "win32")
    monkeypatch.setattr(entry, "run_command", lambda *args: launched.append(args))
    # Act
    result = run_pdf_worker(b"synthetic")
    # Assert
    assert result.outcome is PdfWorkerOutcome.UNSUPPORTED_ENVIRONMENT
    assert result.pages == ()
    assert result.total_pages is None
    assert launched == []
