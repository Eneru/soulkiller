"""PDF parser imports must follow independently tested memory and offline guards."""

import builtins
import runpy
import sys

import pytest

from soulkiller_text import pdf_worker_bootstrap, pdf_worker_candidate

from .pdf_worker_bootstrap_fixtures import LIMIT, install_guard_doubles


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["1"],
        [str(LIMIT), "20", "extra"],
        ["invalid", "20"],
        ["67108863", "20"],
        ["2147483649", "20"],
        [str(LIMIT), "invalid"],
        [str(LIMIT), "0"],
        [str(LIMIT), "21"],
    ],
)
def test_invalid_bootstrap_profile_never_configures_guards_or_imports_candidate(
    arguments: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setattr(sys, "path", list(sys.path))
    configured: list[int] = []
    monkeypatch.setattr(
        pdf_worker_bootstrap, "_configure_guards", lambda limit: configured.append(limit)
    )
    # Act
    code = pdf_worker_bootstrap.main(arguments)
    # Assert
    assert code == 3
    assert configured == []


@pytest.mark.parametrize("failing_guard", ["memory", "network"])
def test_guard_failure_prevents_candidate_import_and_execution(
    failing_guard: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    events: list[str] = []
    original_import = builtins.__import__
    monkeypatch.setattr(sys, "path", list(sys.path))
    install_guard_doubles(
        monkeypatch,
        events,
        memory_supported=failing_guard != "memory",
        network_supported=failing_guard != "network",
    )

    def observed_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if "pdf_worker_candidate" in name or name == "pypdf":
            raise AssertionError("A failed guard must prevent parser-related imports.")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", observed_import)
    # Act
    code = pdf_worker_bootstrap.main([str(LIMIT), "20"])
    # Assert
    assert code == 3
    assert events == (["memory"] if failing_guard == "memory" else ["memory", "network"])


def test_both_guards_precede_candidate_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    events: list[str] = []
    monkeypatch.setattr(sys, "path", list(sys.path))
    install_guard_doubles(monkeypatch, events)

    def candidate(max_pages: int) -> int:
        events.append(f"candidate:{max_pages}")
        return 2

    monkeypatch.setattr(pdf_worker_candidate, "run_candidate", candidate)
    # Act
    code = pdf_worker_bootstrap.main([str(LIMIT), "2"])
    # Assert
    assert code == 2
    assert events == ["memory", "network", "candidate:2"]


def test_allocation_failure_has_reserved_exit_without_raw_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(pdf_worker_bootstrap, "_configure_guards", lambda limit: True)

    def failed(max_pages: int) -> int:
        raise MemoryError("private synthetic allocation diagnostic")

    monkeypatch.setattr(pdf_worker_candidate, "run_candidate", failed)
    # Act
    code = pdf_worker_bootstrap.main([str(LIMIT), "20"])
    # Assert
    assert code == 4


def test_explicit_process_arguments_are_used(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", ["pdf_worker_bootstrap.py", str(LIMIT), "2"])
    monkeypatch.setattr(pdf_worker_bootstrap, "_configure_guards", lambda limit: True)
    monkeypatch.setattr(pdf_worker_candidate, "run_candidate", lambda max_pages: 0)
    # Act
    code = pdf_worker_bootstrap.main()
    # Assert
    assert code == 0


@pytest.mark.parametrize(
    "helper_name", ["pdf_constants", "worker_bootstrap", "worker_network_guard"]
)
def test_script_entry_fails_closed_without_guard_helper(
    helper_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", ["pdf_worker_bootstrap.py", str(LIMIT), "20"])
    original_import = builtins.__import__

    def missing_guard(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == helper_name:
            raise ImportError("private synthetic missing guard")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", missing_guard)
    # Act
    with pytest.raises(SystemExit) as failure:
        runpy.run_path(pdf_worker_bootstrap.__file__, run_name="__main__")
    # Assert
    assert failure.value.code == 3


@pytest.mark.parametrize(
    "helper_name", ["pdf_constants", "worker_bootstrap", "worker_network_guard"]
)
def test_script_entry_contains_allocation_failure_during_guard_helper_import(
    helper_name: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", ["pdf_worker_bootstrap.py", str(LIMIT), "20"])
    original_import = builtins.__import__

    def allocation_failure(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == helper_name:
            raise MemoryError("private synthetic helper allocation diagnostic")
        if "pdf_worker_candidate" in name or name == "pypdf":
            raise AssertionError("An early allocation failure must prevent parser imports.")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", allocation_failure)
    # Act
    with pytest.raises(SystemExit) as failure:
        runpy.run_path(pdf_worker_bootstrap.__file__, run_name="__main__")
    captured = capsys.readouterr()
    # Assert
    assert failure.value.code == 4
    assert captured.out == ""
    assert captured.err == ""
