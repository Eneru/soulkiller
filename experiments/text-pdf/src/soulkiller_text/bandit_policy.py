"""Keep every Bandit finding active except the exact trusted-worker heuristics."""

import ast
import json
import sys
from pathlib import Path

REPORT_LIMIT = 1024 * 1024
SUPERVISOR_PATH = "src/soulkiller_text/supervise.py"
REVIEWED_CALL = """subprocess.Popen(
    command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    shell=False, close_fds=True, start_new_session=True,
    env={"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
)"""


def validate_report(report: object, supervisor_source: str) -> None:
    """Require the two expected locations and exact call syntax; reject all others."""
    if not isinstance(report, dict) or report.get("errors") != []:
        raise ValueError("bandit_policy_failed")
    findings = report.get("results")
    if not isinstance(findings, list) or len(findings) != 2:
        raise ValueError("bandit_policy_failed")
    try:
        tree = ast.parse(supervisor_source)
        expected_call = ast.parse(REVIEWED_CALL, mode="eval").body
    except (SyntaxError, RecursionError):
        raise ValueError("bandit_policy_failed") from None
    imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Import) and any(alias.name == "subprocess" for alias in node.names)
    ]
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "Popen"
    ]
    if len(imports) != 1 or len(calls) != 1:
        raise ValueError("bandit_policy_failed")
    if ast.dump(imports[0]) != ast.dump(ast.parse("import subprocess").body[0]):
        raise ValueError("bandit_policy_failed")
    if ast.dump(calls[0]) != ast.dump(expected_call):
        raise ValueError("bandit_policy_failed")
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_command"
    ]
    if len(functions) != 1 or calls[0] not in list(ast.walk(functions[0])):
        raise ValueError("bandit_policy_failed")
    locations: dict[str, ast.Import | ast.Call] = {"B404": imports[0], "B603": calls[0]}
    seen: set[str] = set()
    for finding in findings:
        if not isinstance(finding, dict) or finding.get("filename") != SUPERVISOR_PATH:
            raise ValueError("bandit_policy_failed")
        identifier = finding.get("test_id")
        line = finding.get("line_number")
        if not isinstance(identifier, str) or identifier not in locations or identifier in seen:
            raise ValueError("bandit_policy_failed")
        node = locations[identifier]
        if type(line) is not int or not node.lineno <= line <= (node.end_lineno or node.lineno):
            raise ValueError("bandit_policy_failed")
        seen.add(identifier)


def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    fields: dict[str, object] = {}
    for key, value in pairs:
        if key in fields:
            raise ValueError("bandit_policy_failed")
        fields[key] = value
    return fields


def _reject_constant(value: str) -> object:
    raise ValueError("bandit_policy_failed")


def main(arguments: list[str] | None = None) -> int:
    """Read an internal bounded scanner report and emit only a safe failure."""
    arguments = sys.argv[1:] if arguments is None else arguments
    try:
        if len(arguments) != 1:
            raise ValueError("bandit_policy_failed")
        with Path(arguments[0]).open("rb") as stream:
            raw = stream.read(REPORT_LIMIT + 1)
        if len(raw) > REPORT_LIMIT:
            raise ValueError("bandit_policy_failed")
        report = json.loads(raw, object_pairs_hook=_unique_fields, parse_constant=_reject_constant)
        source = Path(__file__).with_name("supervise.py").read_text()
        validate_report(report, source)
    except (OSError, ValueError, RecursionError):
        print("Bandit policy failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
