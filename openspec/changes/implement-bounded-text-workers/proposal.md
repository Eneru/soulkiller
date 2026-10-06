# Proposal: bounded TXT worker foundation

## Why

The reviewed extraction evaluation needs execution guards before PDF candidates
are introduced. The existing confined TXT corpus supplies verified byte snapshots;
running its trusted UTF-8 baseline in a bounded child process makes supervision
independently reviewable in this short implementation tranche.

## What Changes

- Add an immutable worker result and validated per-worker limits for the existing
  TXT baseline, preserving source hashes and decoded text.
- Supervise a fixed isolated Python worker with one wall-clock deadline, a Linux
  address-space ceiling, bounded combined output and explicit failure outcomes.
- Test interruption, malformed responses and process cleanup independently from
  PDF parsing, alongside existing Python quality gates.
- Document the delivered boundary and remaining extraction-evaluation work.

## Capabilities

### New Capabilities

- `bounded-text-workers`: bounded execution and verified outcomes for the trusted
  UTF-8 baseline operating on supplied immutable bytes.

### Modified Capabilities

None. This is a partial implementation of the reviewed
[evaluation contract](../evaluate-text-pdf-extraction/specs/text-pdf-extraction-evaluation/spec.md),
without weakening or claiming completion of its full execution boundary.

## Impact

Only the experimental Python package, its synthetic tests and documentation are
affected. No dependency, language, editor integration or CI event change is
needed: the existing pinned CPython runtime and quality tools remain applicable.
No PDF parser, manifest schema extension, filesystem output, runner CLI, scoring,
benchmark, network service, model or provider is added. Python remains an
evaluation tool, not an adopted production stack.
