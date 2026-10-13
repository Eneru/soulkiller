# TXT/PDF evaluation: initial implementation tranches

This is an experimental Python seam, not an application stack or a completed
parser comparison. [The parent plan](../../openspec/changes/evaluate-text-pdf-extraction/design.md)
was approved in PR #13. PR #14 delivers byte-to-TXT decoding, evidence
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

The [confined corpus guide](../../docs/text-corpus-input.md) documents the second
tranche: explicit TXT manifests, verified byte snapshots and independently annotated
literal fixtures. The [third tranche](../../docs/text-worker-supervision.md)
supervises the trusted TXT baseline with explicit process guards. The
[fourth tranche](../../docs/native-pdf-adapter.md) adds the internal pypdf adapter
and independently expected native-page fixtures. The
[fifth tranche](../../docs/pdf-corpus-input.md) adds versioned mixed corpus selection
and independently declared PDF page facts without parsing. The
[sixth tranche](../../docs/pdf-worker-supervision.md) adds the supervised native
PDF byte worker with independent protocol checks and early offline/resource
guards. The [seventh tranche](../../docs/bounded-corpus-run.md) connects verified
snapshots and workers with observed aggregate guards and in-memory interrupted
records. Durable reports and comparisons remain later tranches.

Tests/static analysis are offline. Audit explicitly queries public package
advisory services; it sends package names/versions, not source data. Findings and
service/tool errors fail. There is no CLI ingestion command, report, model download or performance result.
The internal PDF adapter remains a trusted-fixture seam. The public PDF worker
requires an externally supplied network-disabled container; it refuses in the
ordinary connected devcontainer before importing pypdf.

For native VS Code Ruff/mypy diagnostics, source navigation and pytest Test
Explorer, follow [Python editor setup](../../docs/python-editor.md). The full
coverage/security gate remains the canonical CLI/task, not an individual editor
test run.

## API behavior

The public helpers are `soulkiller_text.extract_utf8(bytes)` and
`soulkiller_text.evidence_slice(result, start, end)`. The package lives in `src`;
tests add that path through pyproject.toml without installing the experiment.
Callers can obtain verified bytes with load_corpus(workspace_root, corpus_path).
Its trusted workspace/corpus boundary and exact schema are documented in the
[TXT guide](../../docs/text-corpus-input.md) and
[PDF extension](../../docs/pdf-corpus-input.md); the Linux loader does no source scan.

`run_text_worker(source, limits=None)` supervises the same UTF-8 baseline in a
fixed isolated child. `WorkerLimits` defaults to 60 seconds, 2 GiB virtual address
space and 10 MiB combined output. `WorkerResult` retains the original hash and
exact text only for verified success; timeout, output, protocol and cleanup
failures remain explicit. See the [worker guide](../../docs/text-worker-supervision.md)
for numeric ranges, errors and an actual network-disabled container launch. The
API itself does not disable networking and is not a hostile-parser sandbox.

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
  inline nosec escapes. Only the reviewed fixed-command B404/B603 findings in
  `supervise.py` are accepted through an exact AST-checked exception policy;
  extra/duplicate findings, unsafe call options and scanner errors fail.
  Tests' intentional assertions are outside that scan.
- pip-audit: complete pinned/hash-locked tool graph, strict advisory/error failure.
- Existing Gitleaks/Hadolint/JavaScript/Bash gates remain independent.

[Quality commands](../../docs/quality-checks.md) document hooks, editor tasks
and the existing PR-to-main/SemVer-tag CI lane. No benchmark is a default check.
No web service exists, so ZAP is not applicable. Linux checks do not validate
native Windows performance or the 8/16 GiB CPU-only reference profiles.

## Internal PDF adapter

Base pypdf 6.20.0 is image-installed with its verified wheel hash and no extras.
The internal native_pdf module returns immutable one-based page records, source
revision hashes and explicit outcomes. It runs only against tiny trusted synthetic
fixtures through its internal seam and under the supervised byte worker.
The mixed corpus loader does not invoke it; the separate bounded run dispatches
only the fixed supervised workers.
See [the adapter guide](../../docs/native-pdf-adapter.md) for native extraction
semantics and [PDF worker supervision](../../docs/pdf-worker-supervision.md)
for independently validated responses and offline execution.

## Small follow-ups

The confined TXT corpus and trusted TXT worker foundation are implemented.
Remaining short PRs:

1. Confined persisted reports and interruption records, then independent scoring.
2. Native Docling candidate under the same reviewed run guards.
3. Explicit approved offline Linux comparison; review findings before choosing a stack.

Each tranche gets a tested ready PR and human review before continuing. Native
Windows remains a separate reviewed lane. Detailed parent tasks remain unchecked
until complete, rather than treating this foundation as a finished experiment.
