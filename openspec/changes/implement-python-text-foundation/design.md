# Design

## Scope and authority

The approved parent plan is [evaluate-text-pdf-extraction](../evaluate-text-pdf-extraction/design.md).
PR #13 merge and the 2026-10-05 implementation request authorize this small seam.
Future manifest reads must enforce the parent's confinement and resource guards
before invoking it; this API accepts bytes and performs no I/O.

## Runtime and modules

Build CPython 3.13.16 from its official SHA-256-verified source in an Ubuntu
builder stage. Keep it in /opt/python, with a separate /opt/python-tools venv.
Leave Ubuntu's system interpreter unchanged. Pin/hash every tool dependency
and install wheels only; keep artifact/license inventory and update instructions.
Use separate frozen result/evidence classes and named pure functions.
The source hash describes the original bytes; returned text is never normalized.
An invalid encoding produces a named outcome with no decoded text. Empty bytes
produce no_text; whitespace, BOM and NUL remain text, not guessed encodings.
Evidence records SHA-256, start/end and exact quote; offsets are zero-based,
end-exclusive Unicode code points. No filename is interpreted as authorship.

## Gates and exclusions

Use pinned pytest, coverage.py, Ruff, mypy, Bandit and pip-audit. Measure all
maintained experiment source, including unexecuted modules: >=70% executable
line coverage, independently of JavaScript/Bash. Report branch coverage separately.
Exclude tests, configuration and third-party packages only; no maintained source
exclusions. Use independent synthetic cases and meaningful negative gate probes.
Keep tests/static checks offline; dependency audits explicitly contact advisory
services with public package metadata only and fail on findings/tool errors.
Extend the existing canonical check command and repository-local hook, preserving
its secret scan. Editor tasks reuse the image tools; editor UI is not assumed tested.
Existing unprivileged PR-to-main/SemVer-tag workflow uses those commands, without
new events, expensive benchmarks or credentials. ZAP is inapplicable without web.

## Review sequence

1. This PR: runtime, gates and byte-to-TXT evidence.
2. Next: confined manifest/source reads and independent corpus annotations.
3. Next: one bounded worker and pypdf adapter/error cases.
4. Next: native Docling candidate, scoring and inspectable reports.
5. Then: approved offline Linux comparison; native Windows remains a separate lane.

Each tranche needs its own tested ready PR and maintainer review. Existing parent
tasks remain incomplete until their full criteria are met. Subissues would need
App Issues support; never publish them through the human connector as a fallback.
