"""Independent findings verify the exact worker exception without broad skips."""

import ast
import copy
import json
from pathlib import Path

import pytest

from soulkiller_text import bandit_policy

from .bandit_fixtures import SUPERVISOR_SOURCE, clean_report


def test_only_the_two_exact_trusted_worker_findings_are_accepted() -> None:
    # Arrange
    report = clean_report()
    # Act
    bandit_policy.validate_report(report, SUPERVISOR_SOURCE)
    # Assert
    assert report["errors"] == []


@pytest.mark.parametrize(
    "report",
    [
        None,
        [],
        {},
        {"errors": ["scanner error"], "results": []},
        {"errors": [], "results": []},
        {"errors": [], "results": None},
    ],
)
def test_missing_malformed_or_failed_scan_is_rejected(report: object) -> None:
    # Arrange
    source = SUPERVISOR_SOURCE
    # Act
    with pytest.raises(ValueError, match="^bandit_policy_failed$"):
        bandit_policy.validate_report(report, source)
    # Assert
    assert source == SUPERVISOR_SOURCE


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("test_id", "B301"),
        ("test_id", None),
        ("filename", "src/another.py"),
        ("line_number", True),
        ("line_number", "3"),
        ("line_number", 10000),
    ],
)
def test_unexpected_findings_and_locations_are_rejected(field: str, value: object) -> None:
    # Arrange
    report = clean_report()
    findings = report["results"]
    assert isinstance(findings, list)
    findings[1][field] = value
    # Act
    with pytest.raises(ValueError, match="^bandit_policy_failed$"):
        bandit_policy.validate_report(report, SUPERVISOR_SOURCE)
    # Assert
    assert findings[1][field] == value


def test_a_second_identical_finding_cannot_hide_in_the_exception_policy() -> None:
    # Arrange
    report = clean_report()
    findings = report["results"]
    assert isinstance(findings, list)
    findings.append(copy.deepcopy(findings[1]))
    # Act
    with pytest.raises(ValueError, match="^bandit_policy_failed$"):
        bandit_policy.validate_report(report, SUPERVISOR_SOURCE)
    # Assert
    assert len(findings) == 3


def test_duplicate_identifiers_are_rejected_even_with_two_records() -> None:
    # Arrange
    report = clean_report()
    findings = report["results"]
    assert isinstance(findings, list)
    findings[1] = copy.deepcopy(findings[0])
    # Act
    with pytest.raises(ValueError):
        bandit_policy.validate_report(report, SUPERVISOR_SOURCE)
    # Assert
    assert findings[1]["test_id"] == "B404"


@pytest.mark.parametrize(
    "source",
    [
        SUPERVISOR_SOURCE.replace("shell=False", "shell=True"),
        SUPERVISOR_SOURCE.replace("close_fds=True", "close_fds=False"),
        SUPERVISOR_SOURCE.replace("start_new_session=True", "start_new_session=False"),
        SUPERVISOR_SOURCE.replace("command,", "caller_command,"),
        SUPERVISOR_SOURCE.replace('"C.UTF-8"', '"environment-selected"'),
        SUPERVISOR_SOURCE.replace("import subprocess", "import subprocess as arbitrary"),
        SUPERVISOR_SOURCE + "import subprocess\n",
        SUPERVISOR_SOURCE + "subprocess.Popen(command)\n",
        SUPERVISOR_SOURCE.replace("def run_command", "def another_function"),
        "invalid python source!",
    ],
)
def test_changed_worker_launch_or_additional_imports_calls_are_rejected(source: str) -> None:
    # Arrange
    report = clean_report()
    # Act
    with pytest.raises(ValueError):
        bandit_policy.validate_report(report, source)
    # Assert
    assert source != SUPERVISOR_SOURCE


@pytest.mark.parametrize(
    "payload",
    [
        b"not json",
        b'{"errors":[],"errors":[]}',
        b'{"value":NaN}',
        b'{"value":Infinity}',
        b"\xff",
        b"x" * (1024 * 1024 + 1),
    ],
)
def test_cli_rejects_invalid_or_oversized_reports_without_echoing_content(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    payload: bytes,
) -> None:
    # Arrange
    path = tmp_path / "scanner.json"
    path.write_bytes(payload)
    # Act
    status = bandit_policy.main([str(path)])
    # Assert
    assert status == 1
    assert capsys.readouterr().err == "Bandit policy failed.\n"


def test_cli_reports_missing_file_safely(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    path = tmp_path / "private-scanner.json"
    # Act
    status = bandit_policy.main([str(path)])
    # Assert
    assert status == 1
    assert capsys.readouterr().err == "Bandit policy failed.\n"


@pytest.mark.parametrize("arguments", [[], ["first", "second"]])
def test_cli_rejects_invalid_arguments(
    arguments: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    provided = arguments
    # Act
    status = bandit_policy.main(provided)
    # Assert
    assert status == 1
    assert capsys.readouterr().err == "Bandit policy failed.\n"


def test_cli_accepts_a_report_matching_the_actual_reviewed_source(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange
    source = Path(bandit_policy.__file__).with_name("supervise.py").read_text()
    tree = ast.parse(source)
    imported = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Import) and any(alias.name == "subprocess" for alias in node.names)
    )
    call = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Popen"
    )
    report = {
        "errors": [],
        "results": [
            {
                "test_id": "B404",
                "filename": "src/soulkiller_text/supervise.py",
                "line_number": imported.lineno,
            },
            {
                "test_id": "B603",
                "filename": "src/soulkiller_text/supervise.py",
                "line_number": call.lineno,
            },
        ],
    }
    path = tmp_path / "scanner.json"
    path.write_text(json.dumps(report))
    # Act
    status = bandit_policy.main([str(path)])
    # Assert
    assert status == 0
    assert capsys.readouterr() == ("", "")
