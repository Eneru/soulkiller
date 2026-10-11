"""Fixed-worker integration retains the existing strict TXT semantics."""

import importlib
from typing import cast

import pytest

from soulkiller_text.run_text_worker import run_text_worker
from soulkiller_text.worker_limits import WorkerLimits

from .synthetic_sources import (
    BILINGUAL_BYTES,
    BILINGUAL_SHA256,
    BILINGUAL_TEXT,
    EMPTY_SHA256,
    INVALID_BYTES,
    INVALID_SHA256,
)


@pytest.mark.parametrize(
    ("source", "outcome", "text", "source_hash"),
    [
        (BILINGUAL_BYTES, "success", BILINGUAL_TEXT, BILINGUAL_SHA256),
        (b"", "no_text", None, EMPTY_SHA256),
        (INVALID_BYTES, "invalid_encoding", None, INVALID_SHA256),
    ],
)
def test_fixed_worker_preserves_strict_baseline_outcomes(
    source: bytes,
    outcome: str,
    text: str | None,
    source_hash: str,
) -> None:
    # Arrange
    original = source
    # Act
    result = run_text_worker(original)
    # Assert
    assert result.outcome == outcome
    assert result.text == text
    assert result.source_sha256 == source_hash
    assert original == source


def test_worker_accepts_exact_five_mebibyte_input_boundary() -> None:
    # Arrange
    source = b"\xff" * (5 * 1024**2)
    # Act
    result = run_text_worker(source)
    # Assert
    assert result.outcome == "invalid_encoding"
    assert result.text is None


def test_lower_output_budget_is_enforced_for_real_decoder() -> None:
    # Arrange
    limits = WorkerLimits(output_bytes=1)
    # Act
    result = run_text_worker(BILINGUAL_BYTES, limits)
    # Assert
    assert result.outcome == "output_limit"
    assert result.text is None


def test_minimum_memory_profile_can_run_small_real_decoder() -> None:
    # Arrange
    limits = WorkerLimits(address_space_bytes=64 * 1024**2)
    # Act
    result = run_text_worker(BILINGUAL_BYTES, limits)
    # Assert
    assert result.outcome == "success"
    assert result.text == BILINGUAL_TEXT


def test_nonlinux_environment_fails_closed_without_starting_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    entry = importlib.import_module("soulkiller_text.run_text_worker")
    monkeypatch.setattr(entry.sys, "platform", "win32")
    started: list[object] = []

    def forbidden(*args: object) -> None:
        started.append(args)
        raise AssertionError("Unsupported environment must not launch a worker.")

    monkeypatch.setattr(entry, "run_command", forbidden)
    # Act
    result = run_text_worker(BILINGUAL_BYTES)
    # Assert
    assert result.outcome == "unsupported_environment"
    assert result.source_sha256 == BILINGUAL_SHA256
    assert result.text is None
    assert started == []


def test_invalid_public_limits_object_is_rejected_before_launch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    entry = importlib.import_module("soulkiller_text.run_text_worker")
    started: list[object] = []

    def forbidden(*args: object) -> None:
        started.append(args)
        raise AssertionError("Invalid limits must not launch a worker.")

    monkeypatch.setattr(entry, "run_command", forbidden)
    # Act
    with pytest.raises(ValueError, match="^invalid_worker_limits$"):
        run_text_worker(BILINGUAL_BYTES, cast(WorkerLimits, object()))
    # Assert
    assert started == []


def test_isolated_worker_ignores_inherited_python_startup_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("PYTHONPATH", "/definitely-not-a-soulkiller-module")
    monkeypatch.setenv("PYTHONSTARTUP", "/definitely-not-a-soulkiller-startup")
    # Act
    result = run_text_worker(BILINGUAL_BYTES)
    # Assert
    assert result.outcome == "success"
    assert result.text == BILINGUAL_TEXT
