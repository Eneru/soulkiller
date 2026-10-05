#!/usr/bin/env bash
set -euo pipefail
export GIT_NO_REPLACE_OBJECTS=1 GIT_OPTIONAL_LOCKS=0

fail() { printf '%s\n' "Quality check failed: $1" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || fail "required tool $1 is unavailable"; }

need git
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "run inside a Git repository"
cd -- "$repo"
command_name="${1:-all}"
if [[ $# -gt 0 ]]; then shift; fi

temp=""
cleanup() { if [[ -n "$temp" ]]; then rm -rf -- "$temp"; fi; }
trap cleanup EXIT

prepare_scanner() {
    need gitleaks
    [[ "$(gitleaks version 2>/dev/null)" == "8.30.1" ]] || fail "expected pinned Gitleaks 8.30.1"
    temp="$(mktemp -d)"
}

scan() {
    # Ignore ambient scanner configuration and inline/ignored-file exemptions.
    if ! env -u GITLEAKS_CONFIG -u GITLEAKS_CONFIG_TOML gitleaks \
        --config "$script_dir/gitleaks.toml" --gitleaks-ignore-path /dev/null \
        --ignore-gitleaks-allow --redact --no-banner --exit-code 1 "$@" \
        >"$temp/scanner.log" 2>&1; then
        fail "secret scan rejected content or could not complete (diagnostics withheld)"
    fi
}

scan_index() {
    local index_file index_before index_after
    index_file="$(git rev-parse --git-path index)" || fail "cannot locate the index"
    [[ -f "$index_file" && ! -L "$index_file" ]] || fail "index is missing or unsafe"
    index_before="$(sha256sum -- "$index_file")" || fail "cannot fingerprint the index"
    # Read raw Git blobs: checkout-index would apply user-defined smudge filters.
    git ls-files --stage -z >"$temp/index-entries" 2>/dev/null \
        || fail "cannot enumerate the index"
    mkdir -p "$temp/index"
    local entry metadata mode object stage path
    while IFS= read -r -d '' entry; do
        metadata="${entry%%$'\t'*}"
        path="${entry#*$'\t'}"
        read -r mode object stage <<<"$metadata"
        [[ "$stage" == 0 && "$object" =~ ^[a-f0-9]{40}$ ]] \
            || fail "unmerged or unsupported index entry"
        case "$mode" in 100644|100755) ;; *) fail "indexed symlinks or submodules are unsupported" ;; esac
        case "$path" in ""|/*|..|../*|*/../*|*/..) fail "unsafe indexed path" ;; esac
        [[ ! "$path" =~ [[:cntrl:]] ]] || fail "unsupported indexed path"
        mkdir -p -- "$temp/index/$(dirname -- "$path")"
        git cat-file blob "$object" >"$temp/index/$path" 2>/dev/null \
            || fail "cannot read indexed blob"
    done <"$temp/index-entries"
    scan dir "$temp/index"
    index_after="$(sha256sum -- "$index_file")" || fail "cannot fingerprint the index"
    [[ "$index_before" == "$index_after" ]] || fail "index changed during secret scan"
}

scan_changes() {
    git diff --no-ext-diff --no-textconv --binary HEAD -- >"$temp/tracked.diff" \
        || fail "cannot read tracked changes"
    scan dir "$temp/tracked.diff"
}

docker_checks() {
    need hadolint
    [[ "$(hadolint --version)" == "Haskell Dockerfile Linter 2.15.1" ]] \
        || fail "expected pinned Hadolint 2.15.1"
    local found=0 path
    while IFS= read -r -d '' path; do
        case "$path" in
            Dockerfile|Dockerfile.*|*/Dockerfile|*/Dockerfile.*|*.Dockerfile)
                [[ ! -L "$path" && -f "$path" ]] || fail "unsafe Dockerfile path"
                hadolint --failure-threshold style "$path" || fail "Dockerfile analysis"
                found=1
                ;;
        esac
    done < <(git ls-files --cached --others --exclude-standard -z)
    [[ "$found" -eq 1 ]] || fail "no applicable Dockerfile found"
}

static_checks() {
    docker_checks
    need eslint
    eslint --max-warnings 0 eslint.config.mjs tools/ || fail "JavaScript static analysis"
}

case "$command_name" in
    secrets-staged)
        [[ $# -eq 0 ]] || fail "unexpected arguments"
        prepare_scanner
        scan_index
        ;;
    secrets)
        [[ $# -eq 0 ]] || fail "unexpected arguments"
        prepare_scanner
        scan_index
        scan_changes
        ;;
    secrets-publication)
        body=""
        metadata=0
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --body-file)
                    [[ $# -ge 2 && -z "$body" ]] || fail "provide one body file"
                    body="$2"; shift 2 ;;
                --metadata-stdin)
                    [[ "$metadata" -eq 0 ]] || fail "duplicate metadata flag"
                    metadata=1; shift ;;
                *) fail "unexpected publication-scan argument" ;;
            esac
        done
        [[ -n "$body" && -f "$body" && ! -L "$body" ]] || fail "body file is unavailable or unsafe"
        body="$(realpath -- "$body")" || fail "cannot resolve body file"
        case "$body" in "$repo"/.soulkiller-local/*) ;; *) fail "body file must be in the local repository directory" ;; esac
        git check-ignore --quiet -- "$body" || fail "body file must be ignored"
        prepare_scanner
        scan_index
        scan_changes
        # Copy only the explicitly selected PR body, never its surrounding directory.
        cp -- "$body" "$temp/pull-request-body.txt"
        scan dir "$temp/pull-request-body.txt"
        if [[ "$metadata" -eq 1 ]]; then scan stdin; fi
        ;;
    secrets-history)
        [[ $# -eq 0 ]] || fail "unexpected arguments"
        prepare_scanner
        scan git "$repo"
        ;;
    secrets-changes)
        [[ $# -eq 1 && "$1" =~ ^[a-f0-9]{40}$ && "$1" != 0000000000000000000000000000000000000000 ]] \
            || fail "provide one existing base commit SHA"
        git rev-parse --verify "$1^{commit}" >/dev/null 2>&1 || fail "base commit is unavailable"
        prepare_scanner
        scan git --log-opts="$1..HEAD" "$repo"
        ;;
    docker)
        [[ $# -eq 0 ]] || fail "unexpected arguments"
        docker_checks
        ;;
    static)
        [[ $# -eq 0 ]] || fail "unexpected arguments"
        static_checks
        ;;
    audit)
        [[ $# -eq 0 ]] || fail "unexpected arguments"
        need npm
        npm --prefix /opt/quality audit --audit-level=low --omit=dev \
            --fetch-retries=0 --fetch-timeout=10000 || fail "quality-tool dependency audit"
        npm --prefix tools/github-app audit --audit-level=low \
            --fetch-retries=0 --fetch-timeout=10000 || fail "publisher dependency audit"
        ;;
    selftest)
        [[ $# -eq 0 ]] || fail "unexpected arguments"
        bash "$script_dir/selftest.sh"
        ;;
    coverage)
        [[ $# -eq 0 ]] || fail "unexpected arguments"
        bash "$script_dir/coverage.sh"
        ;;
    python)
        [[ $# -eq 0 ]] || fail "unexpected arguments"
        bash "$script_dir/python.sh" all
        ;;
    all)
        [[ $# -eq 0 ]] || fail "unexpected arguments"
        bash "$script_dir/check.sh" secrets
        if [[ -n "${SOULKILLER_CHECK_BASE:-}" && "$SOULKILLER_CHECK_BASE" != 0000000000000000000000000000000000000000 ]]; then
            bash "$script_dir/check.sh" secrets-changes "$SOULKILLER_CHECK_BASE"
        fi
        static_checks
        bash "$script_dir/python.sh" all
        bash "$script_dir/check.sh" audit
        bash "$script_dir/coverage.sh"
        npm --prefix tools/github-app test
        openspec validate --all --strict --no-interactive
        git diff --check
        git diff --cached --check
        ;;
    *) fail "unknown check; use secrets-staged, secrets, secrets-publication, secrets-history, secrets-changes, docker, static, audit, selftest, coverage, python or all" ;;
esac
printf '%s\n' "Quality check passed: $command_name"
