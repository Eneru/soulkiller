"""Immutable worker models and bounded execution-profile validation."""

from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from soulkiller_text.worker_limits import WorkerLimits
from soulkiller_text.worker_result import WorkerResult

MIB = 1024**2


def test_default_limits_match_reviewed_per_worker_guards() -> None:
    # Arrange / Act
    limits = WorkerLimits()
    # Assert
    assert limits.wall_seconds == 60
    assert limits.address_space_bytes == 2 * 1024**3
    assert limits.output_bytes == 10 * MIB


@pytest.mark.parametrize("wall", [0.001, 1, 60])
def test_wall_time_accepts_positive_finite_values_up_to_ceiling(wall: float) -> None:
    # Arrange / Act
    limits = WorkerLimits(wall_seconds=wall)
    # Assert
    assert limits.wall_seconds == wall


@pytest.mark.parametrize(
    "wall",
    [
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
        pytest.param(60.001, id="above-ceiling"),
        pytest.param(float("inf"), id="positive-infinity"),
        pytest.param(float("-inf"), id="negative-infinity"),
        pytest.param(float("nan"), id="nan"),
        pytest.param(True, id="boolean"),
        pytest.param("1", id="string"),
        pytest.param(None, id="none"),
        pytest.param(10**1000, id="unbounded-integer"),
    ],
)
def test_invalid_wall_time_is_rejected(wall: object) -> None:
    # Arrange / Act / Assert
    with pytest.raises(ValueError):
        WorkerLimits(wall_seconds=cast(float, wall))


@pytest.mark.parametrize("memory", [64 * MIB, 128 * MIB, 2 * 1024**3])
def test_memory_accepts_integer_reviewed_bounds(memory: int) -> None:
    # Arrange / Act
    limits = WorkerLimits(address_space_bytes=memory)
    # Assert
    assert limits.address_space_bytes == memory


@pytest.mark.parametrize(
    "memory",
    [64 * MIB - 1, 2 * 1024**3 + 1, 0, -1, True, 64.0 * MIB, "67108864", None],
)
def test_invalid_memory_limit_is_rejected(memory: object) -> None:
    # Arrange / Act / Assert
    with pytest.raises(ValueError):
        WorkerLimits(address_space_bytes=cast(int, memory))


@pytest.mark.parametrize("output", [1, 1024, 10 * MIB])
def test_output_accepts_integer_reviewed_bounds(output: int) -> None:
    # Arrange / Act
    limits = WorkerLimits(output_bytes=output)
    # Assert
    assert limits.output_bytes == output


@pytest.mark.parametrize("output", [0, -1, 10 * MIB + 1, True, 1.0, "1", None])
def test_invalid_output_limit_is_rejected(output: object) -> None:
    # Arrange / Act / Assert
    with pytest.raises(ValueError):
        WorkerLimits(output_bytes=cast(int, output))


@pytest.mark.parametrize("attribute", ["wall_seconds", "address_space_bytes", "output_bytes"])
def test_worker_limits_are_immutable(attribute: str) -> None:
    # Arrange
    limits = WorkerLimits()
    # Act / Assert
    with pytest.raises(FrozenInstanceError):
        setattr(limits, attribute, 1)


@pytest.mark.parametrize("attribute", ["outcome", "source_sha256", "text"])
def test_worker_result_is_immutable(attribute: str) -> None:
    # Arrange
    result = WorkerResult("success", "0" * 64, "invented")
    # Act / Assert
    with pytest.raises(FrozenInstanceError):
        setattr(result, attribute, "changed")
