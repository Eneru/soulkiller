#!/usr/bin/env bash
set -euo pipefail

fail() { printf '%s\n' "Python check failed: $1" >&2; exit 1; }
[[ $# -le 1 ]] || fail "unexpected arguments"
command_name="${1:-all}"
case "$command_name" in static|tests|audit|all) ;; *) fail "use static, tests, audit or all" ;; esac
command -v python >/dev/null 2>&1 || fail "the image Python is unavailable"
[[ "$(python --version)" == "Python 3.13.16" ]] || fail "expected isolated Python 3.13.16"
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd -- "$repo/experiments/text-pdf"
[[ -d src && -d tests ]] || fail "experiment source/tests are unavailable"
temp="$(mktemp -d /tmp/soulkiller-python-check.XXXXXX)"
trap 'rm -rf -- "$temp"' EXIT
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export MYPY_CACHE_DIR="$temp/mypy" PYTHONPYCACHEPREFIX="$temp/pycache"
export COVERAGE_FILE="$temp/line.coverage"

static_checks() {
    python -m ruff check --no-cache src tests
    python -m ruff format --check --no-cache src tests
    python -m mypy --config-file pyproject.toml src tests
    # Scan every finding; allow only the two AST-checked fixed-worker heuristics.
    local bandit_status=0
    python -m bandit --quiet --ignore-nosec --recursive src \
        --format json --output "$temp/bandit.json" || bandit_status=$?
    [[ "$bandit_status" -eq 0 || "$bandit_status" -eq 1 ]] || fail "Bandit execution error"
    PYTHONPATH="$repo/experiments/text-pdf/src" \
        python -m soulkiller_text.bandit_policy "$temp/bandit.json"
}
test_checks() {
    # The threshold measures executable lines alone. Branches are a separate report.
    python -m coverage run --rcfile=pyproject.toml -m pytest -p no:cacheprovider
    python -m coverage report --rcfile=pyproject.toml --fail-under=70
    export COVERAGE_FILE="$temp/branch.coverage"
    python -m coverage run --rcfile=pyproject.toml --branch -m pytest -p no:cacheprovider
    python -m coverage report --rcfile=pyproject.toml
}
audit_checks() {
    python -m pip check
    python -m pip_audit --strict --require-hashes --disable-pip \
        --requirement "$repo/.devcontainer/python/requirements.lock" \
        --timeout 10 --progress-spinner off --cache-dir "$temp/audit"
}
case "$command_name" in
    static) static_checks ;;
    tests) test_checks ;;
    audit) audit_checks ;;
    all) static_checks; test_checks; audit_checks ;;
esac
printf '%s\n' "Python check passed: $command_name"
