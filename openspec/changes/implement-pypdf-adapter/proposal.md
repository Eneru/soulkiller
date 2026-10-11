# Proposal: native pypdf adapter foundation

## Why

PR #16 completes trusted TXT worker supervision. The approved extraction
evaluation now needs a small, independently tested native PDF adapter before
integrating a second result protocol and PDF corpus scheduling.

## What Changes

- Add an internal immutable-byte pypdf adapter with one-based page text and
  explicit native-text, protected/malformed, page-limit and partial outcomes.
- Add independently authored bilingual and failure fixtures through a reviewed,
  deterministic synthetic PDF writer included in maintained-source coverage.
- Provision base pypdf 6.20.0 in the existing isolated Python image, pinned by
  wheel hash and inventoried with its license. This updates the plan's 6.19.0
  metadata snapshot because 6.20.0 adds stream-decoding security guards.
- Exercise the adapter on tiny trusted fixtures in a bounded network-disabled
  test container; retain native editor, security and coverage integration.

## Capabilities

### New Capabilities

- `native-pdf-adapter`: internal native page extraction and synthetic-fixture
  contracts for the approved evaluation.

### Modified Capabilities

None. The existing TXT corpus and worker APIs remain unchanged.

## Impact

Python experiment modules/tests, the image's Python hash lock, documentation
and CHANGELOG. No application-language adoption, PDF ingestion CLI, PDF manifest
extension, PDF worker/protocol integration, Docling, scoring, reports,
benchmarks, OCR, model, external helper, provider or paid call is delivered.
These remain subsequent short reviewed tranches of
[evaluate-text-pdf-extraction](../evaluate-text-pdf-extraction/proposal.md).
