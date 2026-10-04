#!/usr/bin/env bash
# Synthetic test runner: coverage assertions are implemented in coverage.mjs.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd -- "$script_dir/../.." && pwd)"
command -v kcov >/dev/null 2>&1 || { echo 'Coverage check failed: kcov is unavailable' >&2; exit 1; }
[[ "$(kcov --version)" == "kcov 43" ]] || { echo 'Coverage check failed: expected pinned kcov 43' >&2; exit 1; }
temp="$(mktemp -d /tmp/soulkiller-coverage.XXXXXX)"
trap 'rm -rf -- "$temp"' EXIT
cd -- "$repo"
node --test --experimental-test-coverage --test-coverage-lines=70 \
    --test-coverage-include=tools/checks/coverage.mjs tools/checks/test/coverage.test.mjs
node --test --experimental-test-coverage --test-coverage-lines=70 \
    --test-coverage-include="tools/checks/ci-policy*.mjs" \
    --test-coverage-exclude="tools/checks/test/**" tools/checks/test/ci-policy*.test.mjs
kcov --bash-method=PS4 \
    --include-pattern=/tools/checks/check.sh,/tools/checks/install-hooks.sh,/.githooks/pre-commit \
    "$temp/report" "$script_dir/selftest.sh"
node "$script_dir/coverage.mjs" "$temp/report/selftest.sh/coverage.json"
