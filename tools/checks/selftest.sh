#!/usr/bin/env bash
set -euo pipefail
unset GIT_INDEX_FILE GIT_DIR GIT_WORK_TREE GIT_NO_REPLACE_OBJECTS

source_repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
temp="$(mktemp -d)"
trap 'rm -rf -- "$temp"' EXIT
secret="$(printf '%s%s' 'gh''p_' 'A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8')"
app_token="$(printf '%s_%s_%s.%s.%s' 'ghs' '5174172' 'eyJhbGciOiJSUzI1NiJ9' 'eyJzdWIiOiJzeW50aGV0aWMifQ' 'ZmFrZS1zaWduYXR1cmU')"
passed=0

fail() { printf '%s\n' "Quality self-test failed: $1" >&2; exit 1; }
pass() { passed=$((passed + 1)); printf '%s\n' "PASS: $1"; }
expect_failure() {
    local name="$1"; shift
    if "$@" >"$temp/output.log" 2>&1; then fail "$name unexpectedly succeeded"; fi
    if rg --quiet --fixed-strings -e "$secret" -e "$app_token" -- "$temp/output.log"; then
        fail "$name exposed synthetic secret diagnostics"
    fi
    pass "$name"
}
fixture() {
    repo="$temp/$1"
    mkdir -p "$repo/tools" "$repo/.soulkiller-local"
    cp -R "$source_repo/tools/checks" "$repo/tools/checks"
    cp -R "$source_repo/.githooks" "$repo/.githooks"
    cd -- "$repo"
    git init --quiet --initial-branch=feature/quality-fixture
    git config --local user.name "Synthetic fixture"
    git config --local user.email "fixture@example.invalid"
    printf '%s\n' '.soulkiller-local/' >.gitignore
    printf '%s\n' 'clean source' >sample.txt
    git add -- .gitignore sample.txt tools .githooks
    git commit --quiet -m "Create synthetic quality fixture"
}

fixture staging
bash tools/checks/install-hooks.sh >"$temp/setup.log"
[[ "$(git config --local --get core.hooksPath)" == ".githooks" ]] || fail "hooks not configured locally"
bash tools/checks/install-hooks.sh >"$temp/setup.log"
pass "explicit and idempotent repository-local hook setup"

printf '%s\n' 'clean staged update' >sample.txt
git add -- sample.txt
printf '%s\n' "$secret" >sample.txt
git commit --quiet -m "Commit only clean staged content" >"$temp/output.log" 2>&1 \
    || fail "unstaged content incorrectly rejected a clean staged commit"
[[ "$(git show HEAD:sample.txt)" == 'clean staged update' ]] || fail "commit did not preserve staged contents"
[[ "$(cat sample.txt)" == "$secret" ]] || fail "hook changed unstaged work"
pass "clean partial staging preserves unstaged work"

git add -- sample.txt
printf '%s\n' 'clean working copy' >sample.txt
head_before="$(git rev-parse HEAD)"
expect_failure "staged synthetic secret rejects commit despite clean worktree" \
    git commit --quiet -m "Attempt synthetic secret commit"
[[ "$(git rev-parse HEAD)" == "$head_before" ]] || fail "failed hook changed history"

git add -- sample.txt
bash tools/checks/check.sh secrets-staged >"$temp/output.log" 2>&1
pass "clean staged index succeeds"

printf '%s\n' 'ordinary proposed PR body' >.soulkiller-local/body.md
bash tools/checks/check.sh secrets-publication --body-file "$repo/.soulkiller-local/body.md" \
    >"$temp/output.log" 2>&1
pass "clean publication body succeeds"

printf '%s\n' "$secret" >.soulkiller-local/body.md
expect_failure "synthetic secret in explicit PR body is rejected" \
    bash tools/checks/check.sh secrets-publication --body-file "$repo/.soulkiller-local/body.md"
printf '%s\n' 'ordinary proposed PR body' >.soulkiller-local/body.md
expect_failure "synthetic secret in PR title is rejected" \
    bash tools/checks/check.sh secrets-publication --body-file "$repo/.soulkiller-local/body.md" --metadata-stdin <<<"$secret"
expect_failure "synthetic secret in commit message is rejected" \
    bash tools/checks/check.sh secrets-publication --body-file "$repo/.soulkiller-local/body.md" --metadata-stdin <<<"chore: $secret"

printf '%s\n' "$secret" >sample.txt
expect_failure "tracked unstaged synthetic secret is rejected" bash tools/checks/check.sh secrets
printf '%s\n' 'clean working copy' >sample.txt

expect_failure "missing scanner fails closed" \
    env PATH=/usr/bin:/bin /bin/bash tools/checks/check.sh secrets-staged
mkdir -p "$temp/failing-tool"
printf '%s\n' '#!/bin/bash' 'if [[ "$1" == version ]]; then echo 8.30.1; else exit 42; fi' >"$temp/failing-tool/gitleaks"
chmod 0755 "$temp/failing-tool/gitleaks"
expect_failure "scanner execution failure fails closed" \
    env PATH="$temp/failing-tool:$PATH" bash tools/checks/check.sh secrets-staged


fixture installation-tokens
printf '%s\n' "$app_token" >new-token.txt
git add -- new-token.txt
expect_failure "new-format staged installation token is rejected" bash tools/checks/check.sh secrets-staged
printf '%s\n' 'clean token fixture' >new-token.txt
git add -- new-token.txt
printf '%s\n' "$app_token" >.soulkiller-local/body.md
expect_failure "new-format installation token in PR body is rejected" \
    bash tools/checks/check.sh secrets-publication --body-file "$repo/.soulkiller-local/body.md"
printf '%s\n' 'clean proposed PR body' >.soulkiller-local/body.md
expect_failure "new-format installation token in PR title is rejected" \
    bash tools/checks/check.sh secrets-publication --body-file "$repo/.soulkiller-local/body.md" --metadata-stdin <<<"$app_token"
expect_failure "new-format installation token in commit message is rejected" \
    bash tools/checks/check.sh secrets-publication --body-file "$repo/.soulkiller-local/body.md" --metadata-stdin <<<"chore: $app_token"

fixture preserve-hooks
printf '%s\n' '#!/bin/bash' 'echo existing-hook' >.git/hooks/pre-commit
previous="$(sha256sum .git/hooks/pre-commit)"
expect_failure "existing unrelated hook is preserved" bash tools/checks/install-hooks.sh
[[ "$(sha256sum .git/hooks/pre-commit)" == "$previous" ]] || fail "existing hook was overwritten"
if git config --local --get core.hooksPath >/dev/null; then fail "rejected setup modified configuration"; fi

fixture preserve-path
git config --local core.hooksPath .existing-hooks
expect_failure "existing hooksPath is preserved" bash tools/checks/install-hooks.sh
[[ "$(git config --local --get core.hooksPath)" == ".existing-hooks" ]] || fail "existing hooksPath changed"

fixture unsafe-links
printf '%s\n' "$secret" >"$temp/outside.txt"
ln -s "$temp/outside.txt" linked-source.txt
git add -- linked-source.txt
expect_failure "indexed symlink is rejected without following it" bash tools/checks/check.sh secrets-staged


fixture smudge-filter
printf '%s\n' 'sample.txt filter=quality-fixture' >.gitattributes
git config --local filter.quality-fixture.clean cat
git config --local filter.quality-fixture.smudge "sed s/$secret/clean-smudged/g"
printf '%s\n' "$secret" >sample.txt
git add -- .gitattributes sample.txt
mkdir -p "$temp/smudged"
git checkout-index --all --prefix="$temp/smudged/" >/dev/null
[[ "$(cat "$temp/smudged/sample.txt")" == "clean-smudged" ]] || fail "smudge-filter fixture was ineffective"
[[ "$(git cat-file blob :sample.txt)" == "$secret" ]] || fail "staged fixture was transformed"
expect_failure "raw staged secret is rejected despite checkout smudge filters" \
    bash tools/checks/check.sh secrets-staged


fixture replacement-objects
printf '%s\n' "$secret" >sample.txt
git add -- sample.txt
secret_object="$(git rev-parse :sample.txt)"
clean_object="$(printf '%s\n' 'replacement-clean' | git hash-object -w --stdin)"
git replace "$secret_object" "$clean_object"
[[ "$(git cat-file blob "$secret_object")" == "replacement-clean" ]] || fail "replacement fixture was ineffective"
expect_failure "raw staged secret is rejected despite replacement objects" \
    bash tools/checks/check.sh secrets-staged

fixture body-links
ln -s "$temp/outside.txt" .soulkiller-local/body-link.md
expect_failure "symlink PR body is rejected" \
    bash tools/checks/check.sh secrets-publication --body-file "$repo/.soulkiller-local/body-link.md"
expect_failure "external PR body is rejected" \
    bash tools/checks/check.sh secrets-publication --body-file "$temp/outside.txt"

fixture dockerfiles
printf '%s\n' 'FROM ubuntu:24.04' 'USER 1000:1000' >Dockerfile
bash tools/checks/check.sh docker >"$temp/output.log" 2>&1 || fail "clean Dockerfile rejected"
pass "clean Dockerfile succeeds"
printf '%s\n' 'FROM ubuntu:latest' 'RUN apt-get update' >Dockerfile.invalid
expect_failure "Hadolint rejects an additional invalid Dockerfile" bash tools/checks/check.sh docker
expect_failure "invalid history base fails closed" \
    bash tools/checks/check.sh secrets-changes untrusted-value


fixture command-boundaries
printf '%s\n' 'clean proposed PR body' >.soulkiller-local/body.md
printf '%s\n' "$secret" >.soulkiller-local/adjacent-private.txt
bash tools/checks/check.sh secrets-publication --body-file "$repo/.soulkiller-local/body.md" >"$temp/output.log" 2>&1
pass "publication scans only the selected body and preserves adjacent ignored private files"
bash tools/checks/check.sh secrets-history >"$temp/output.log" 2>&1
pass "clean synthetic history succeeds"
bash tools/checks/check.sh secrets-changes "$(git rev-parse HEAD)" >"$temp/output.log" 2>&1
pass "valid bounded history range succeeds"
expect_failure "unknown check is rejected" bash tools/checks/check.sh untrusted-command
expect_failure "unexpected staged scan arguments are rejected" bash tools/checks/check.sh secrets-staged untrusted-argument
expect_failure "duplicate publication body argument is rejected" bash tools/checks/check.sh secrets-publication \
    --body-file "$repo/.soulkiller-local/body.md" --body-file "$repo/.soulkiller-local/body.md"

printf '%s\n' "Quality self-tests passed: $passed cases."
