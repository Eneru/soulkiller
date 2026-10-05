# TXT/PDF evaluation: first implementation tranche

This is an experimental Python seam, not an application stack or a completed
parser comparison. [The parent plan](../../openspec/changes/evaluate-text-pdf-extraction/design.md)
was approved in PR #13. This first small PR delivers byte-to-TXT decoding, evidence
and quality gates; see [its contract](../../openspec/changes/implement-python-text-foundation/specs/text-evidence-foundation/spec.md).

## Run in the rebuilt devcontainer

Python 3.13.16 and development tools are image-installed and isolated from Ubuntu's
system Python. No host Python, credentials, LLM or package installation is needed.

From the repository root:

```sh
bash tools/checks/python.sh static
bash tools/checks/python.sh tests
bash tools/checks/python.sh audit
bash tools/checks/check.sh all
```

Tests/static analysis are offline. Audit explicitly queries public package
advisory services; it sends package names/versions, not source data. Findings and
service/tool errors fail. There is no PDF parser, manifest, file reader, worker,
CLI ingestion command, report, model download or performance result yet.

## API behavior

The public helpers are `soulkiller_text.extract_utf8(bytes)` and
`soulkiller_text.evidence_slice(result, start, end)`. The package lives in `src`;
tests add that path through pyproject.toml without installing the experiment.
Callers must provide bytes from a later reviewed and confined input reader.

Decoding retains the original SHA-256 and unchanged UTF-8 text. Empty bytes
produce `no_text`; invalid UTF-8 produces `invalid_encoding` with no decoded text.
Whitespace, BOM, NUL, accents, LF/CRLF and combining characters are preserved.
There is no replacement, guessed encoding, normalization, authorship inference
or persona-memory promotion. Result/evidence records are frozen. Their public
constructors are value containers, not authenticity or validation boundaries.

Evidence holds the original hash, exact quote and zero-based, end-exclusive
Unicode code-point offsets. A multi-byte character occupies one code point; a
combining mark is a separate code point. Invalid integers/ranges or non-success
results never yield evidence. Invalid offset types (including bool) raise
TypeError; empty/negative/reversed/out-of-range spans or failed outcomes raise
ValueError. Callers should use the extraction helper rather than forge records.

## Quality and limits

- pytest: independent synthetic Arrange/Act/Assert scenarios, no personal data.
- coverage.py: >=70% executable **line** coverage for the component aggregate, including every maintained source
  listed by `source=["src"]`, including modules never imported. The current
  component has no maintained-source exclusions. Tests, config and third-party
  packages are outside that denominator. A second small run reports branches
  separately so a combined branch metric cannot replace the line gate.
- Ruff: selected E/F/I/UP/B rules and formatting; mypy: strict source/test types.
- Bandit: all default severity/confidence findings in maintained source, ignoring
  inline nosec escapes. Tests' intentional assertions are outside that scan.
- pip-audit: complete pinned/hash-locked tool graph, strict advisory/error failure.
- Existing Gitleaks/Hadolint/JavaScript/Bash gates remain independent.

[Quality commands](../../docs/quality-checks.md) document hooks, editor tasks
and the existing PR-to-main/SemVer-tag CI lane. No benchmark is a default check.
No web service exists, so ZAP is not applicable. Linux checks do not validate
native Windows performance or the 8/16 GiB CPU-only reference profiles.

## Small follow-ups

1. Confined manifest/source reads, independent fixture bytes and annotations.
2. Bounded worker, pypdf and failure-containment tests.
3. Native Docling candidate, scoring and bounded inspectable reports.
4. Explicit approved offline Linux comparison; review findings before choosing a stack.

Each tranche gets a tested ready PR and human review before continuing. Native
Windows remains a separate reviewed lane. Detailed parent tasks remain unchecked
until complete, rather than treating this foundation as a finished experiment.
