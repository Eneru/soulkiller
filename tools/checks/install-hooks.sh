#!/usr/bin/env bash
set -euo pipefail

fail() { printf '%s\n' "Hook setup refused: $1" >&2; exit 1; }
repo="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "run inside a Git repository"
cd -- "$repo"
[[ -f .githooks/pre-commit && ! -L .githooks/pre-commit ]] || fail "owned pre-commit hook is missing"
configured="$(git config --get core.hooksPath || true)"
if [[ -n "$configured" ]]; then
    [[ "$configured" == ".githooks" ]] || fail "an existing hooksPath must be preserved"
    printf '%s\n' "Soulkiller hooks are already configured."
    exit 0
fi
hooks="$(git rev-parse --git-path hooks)"
if [[ -d "$hooks" ]]; then
    shopt -s nullglob dotglob
    for hook in "$hooks"/*; do
        case "$hook" in *.sample) continue ;; esac
        fail "existing hooks must be preserved"
    done
fi
git config --local core.hooksPath .githooks
printf '%s\n' "Configured repository-local Soulkiller hooks."
