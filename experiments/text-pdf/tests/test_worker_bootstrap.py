"""Child guard setup is tested without changing pytest's own resource limits."""

import resource
import runpy
import sys
from pathlib import Path

import pytest

from soulkiller_text import worker_bootstrap, worker_candidate

LIMIT = 64 * 1024**2


def test_address_space_setup_requires_exact_readback(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    requested: list[tuple[int, tuple[int, int]]] = []
    monkeypatch.setattr(
        resource,
        "setrlimit",
        lambda kind, limits: requested.append((kind, limits)),
    )
    monkeypatch.setattr(resource, "getrlimit", lambda kind: (LIMIT, LIMIT))
    # Act
    supported = worker_bootstrap._configure_address_space(LIMIT)
    # Assert
    assert supported
    assert requested == [(resource.RLIMIT_AS, (LIMIT, LIMIT))]


def test_changed_address_space_readback_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setattr(resource, "setrlimit", lambda *args: None)
    monkeypatch.setattr(resource, "getrlimit", lambda kind: (LIMIT + 1, LIMIT))
    # Act
    supported = worker_bootstrap._configure_address_space(LIMIT)
    # Assert
    assert not supported


@pytest.mark.parametrize("exception", [OSError, ValueError])
def test_address_space_setup_errors_are_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    exception: type[Exception],
) -> None:
    # Arrange
    def failed(*args: object) -> None:
        raise exception("private synthetic resource diagnostic")

    monkeypatch.setattr(resource, "setrlimit", failed)
    # Act
    supported = worker_bootstrap._configure_address_space(LIMIT)
    # Assert
    assert not supported


def test_readback_error_also_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setattr(resource, "setrlimit", lambda *args: None)

    def failed(*args: object) -> tuple[int, int]:
        raise OSError("private synthetic resource diagnostic")

    monkeypatch.setattr(resource, "getrlimit", failed)
    # Act
    supported = worker_bootstrap._configure_address_space(LIMIT)
    # Assert
    assert not supported


@pytest.mark.parametrize(
    "arguments", [[], ["1", "2"], ["not-a-number"], ["0"], ["67108863"], ["2147483649"]]
)
def test_invalid_bootstrap_arguments_do_not_configure_or_decode(
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
) -> None:
    # Arrange
    configured: list[int] = []
    monkeypatch.setattr(
        worker_bootstrap,
        "_configure_address_space",
        lambda limit: configured.append(limit),
    )
    # Act
    exit_code = worker_bootstrap.main(arguments)
    # Assert
    assert exit_code == 3
    assert configured == []


def test_unavailable_guard_prevents_candidate_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    decoded: list[object] = []
    monkeypatch.setattr(worker_bootstrap, "_configure_address_space", lambda limit: False)

    def forbidden() -> int:
        decoded.append(None)
        raise AssertionError("No candidate may run before its resource guard.")

    monkeypatch.setattr(worker_candidate, "run_candidate", forbidden)
    # Act
    exit_code = worker_bootstrap.main([str(LIMIT)])
    # Assert
    assert exit_code == 3
    assert decoded == []


def test_candidate_runs_only_after_successful_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    events: list[str] = []
    monkeypatch.setattr(sys, "path", list(sys.path))

    def configure(limit: int) -> bool:
        events.append("guard")
        return True

    def candidate() -> int:
        events.append("candidate")
        return 2

    monkeypatch.setattr(worker_bootstrap, "_configure_address_space", configure)
    monkeypatch.setattr(worker_candidate, "run_candidate", candidate)
    # Act
    exit_code = worker_bootstrap.main([str(LIMIT)])
    # Assert
    assert exit_code == 2
    assert events == ["guard", "candidate"]
    assert sys.path[0] == str(Path(worker_bootstrap.__file__).parent.parent)


def test_explicit_candidate_allocation_failure_has_reserved_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(worker_bootstrap, "_configure_address_space", lambda limit: True)

    def failed() -> int:
        raise MemoryError("private synthetic allocation diagnostic")

    monkeypatch.setattr(worker_candidate, "run_candidate", failed)
    # Act
    exit_code = worker_bootstrap.main([str(LIMIT)])
    # Assert
    assert exit_code == 4


def test_bootstrap_uses_its_explicit_process_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", ["worker_bootstrap.py", str(LIMIT)])
    monkeypatch.setattr(worker_bootstrap, "_configure_address_space", lambda limit: True)
    monkeypatch.setattr(worker_candidate, "run_candidate", lambda: 0)
    # Act
    exit_code = worker_bootstrap.main()
    # Assert
    assert exit_code == 0


def test_script_entry_exits_safely_when_resource_setup_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setattr(sys, "argv", ["worker_bootstrap.py", str(LIMIT)])

    def failed(*args: object) -> None:
        raise OSError("synthetic unsupported guard")

    monkeypatch.setattr(resource, "setrlimit", failed)
    # Act
    with pytest.raises(SystemExit) as failure:
        runpy.run_path(worker_bootstrap.__file__, run_name="__main__")
    # Assert
    assert failure.value.code == 3
