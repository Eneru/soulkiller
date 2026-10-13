"""Immutable bounded run profiles reject invalid values before source access."""

from dataclasses import FrozenInstanceError
from importlib import import_module
from pathlib import Path
from typing import cast

import pytest

from soulkiller_text.run_corpus import run_corpus
from soulkiller_text.run_limits import RunLimits
from soulkiller_text.worker_limits import WorkerLimits


@pytest.mark.parametrize("wall", [0.001, 1, 600])
def test_positive_finite_wall_budget_within_run_ceiling_is_accepted(wall: float) -> None:
    # Arrange / Act
    limits = RunLimits(wall_seconds=wall)
    # Assert
    assert limits.wall_seconds == wall


@pytest.mark.parametrize(
    "wall", [0, -1, 600.001, float("inf"), float("-inf"), float("nan"), True, "1", None, 10**1000]
)
def test_invalid_run_deadline_is_rejected(wall: object) -> None:
    # Arrange / Act / Assert
    with pytest.raises(ValueError):
        RunLimits(wall_seconds=cast(float, wall))


@pytest.mark.parametrize("output", [1, 1024, 50 * 1024**2])
def test_integer_output_budget_up_to_reviewed_ceiling_is_accepted(output: int) -> None:
    # Arrange / Act
    limits = RunLimits(output_bytes=output)
    # Assert
    assert limits.output_bytes == output


@pytest.mark.parametrize("output", [0, -1, 50 * 1024**2 + 1, True, 1.0, "1", None])
def test_invalid_aggregate_output_budget_is_rejected(output: object) -> None:
    # Arrange / Act / Assert
    with pytest.raises(ValueError):
        RunLimits(output_bytes=cast(int, output))


@pytest.mark.parametrize("worker", [None, {}, object(), 60])
def test_non_worker_profile_cannot_be_embedded_in_run_limits(worker: object) -> None:
    # Arrange / Act / Assert
    with pytest.raises(ValueError):
        RunLimits(worker_limits=cast(WorkerLimits, worker))


def test_default_run_profile_keeps_reviewed_worker_and_aggregate_ceiling() -> None:
    # Arrange / Act
    limits = RunLimits()
    # Assert
    assert limits.wall_seconds == 600
    assert limits.output_bytes == 50 * 1024**2
    assert limits.worker_limits == WorkerLimits()


@pytest.mark.parametrize("field", ["wall_seconds", "output_bytes", "worker_limits"])
def test_run_limits_are_immutable(field: str) -> None:
    # Arrange
    limits = RunLimits()
    # Act / Assert
    with pytest.raises(FrozenInstanceError):
        setattr(limits, field, None)


@pytest.mark.parametrize("invalid", [object(), {}, 1, True, WorkerLimits()])
def test_invalid_public_profile_fails_before_manifest_or_worker_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid: object
) -> None:
    # Arrange
    entry = import_module("soulkiller_text.run_corpus")
    reads: list[object] = []

    def forbidden_load(*args: object) -> None:
        reads.append(args)
        raise AssertionError("Invalid profiles must not read a manifest.")

    monkeypatch.setattr(entry, "load_corpus", forbidden_load)
    # Act
    with pytest.raises(ValueError):
        run_corpus(tmp_path, "missing-corpus", cast(RunLimits, invalid))
    # Assert
    assert reads == []


@pytest.mark.parametrize(
    "field,value", [("wall_seconds", 0), ("output_bytes", True), ("address_space_bytes", 1)]
)
def test_embedding_a_forged_worker_profile_revalidates_every_guard(
    field: str, value: object
) -> None:
    # Arrange
    worker = WorkerLimits()
    object.__setattr__(worker, field, value)
    # Act / Assert
    with pytest.raises(ValueError):
        RunLimits(worker_limits=worker)


@pytest.mark.parametrize(
    "field,value", [("wall_seconds", 0), ("output_bytes", True), ("worker_limits", None)]
)
def test_forged_run_profile_fails_before_reading_any_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    # Arrange
    limits = RunLimits()
    object.__setattr__(limits, field, value)
    entry = import_module("soulkiller_text.run_corpus")
    reads: list[object] = []

    def forbidden_load(*args: object) -> None:
        reads.append(args)
        raise AssertionError("Forged profiles must not read source bytes.")

    monkeypatch.setattr(entry, "load_corpus", forbidden_load)
    # Act
    with pytest.raises(ValueError):
        run_corpus(tmp_path, "missing-corpus", limits)
    # Assert
    assert reads == []
