# Proposal: confined synthetic PDF corpus inputs

## Why
PR #17 completes the internal pypdf adapter. The approved extraction evaluation
next needs explicit PDF source selection and independent page facts before
supervised parsing. Keep this corpus-only tranche small for maintainer review.

## What Changes
- Add explicit schema version 2 for mixed synthetic TXT/PDF manifests while
  preserving version 1 and its TXT-only parser contract.
- Add separate frozen PDF fixture/fact models and permit verified loaded records
  to retain either source type.
- Validate declared PDF page budgets and independent fact/page labels; load exact
  confined byte snapshots and hashes without invoking a PDF parser.
- Reuse the existing runtime/editor/security/coverage integration and document
  deferred PDF extraction checks.

## Capabilities
### New Capabilities
- `pdf-corpus-input`: versioned mixed selection, independent physical-page facts
  and parser-free verified PDF snapshots.
### Modified Capabilities
None. Version-1 TXT semantics and the existing worker protocol remain unchanged.

## Impact
Python corpus models/validation/loading, independent tests and English guides.
No new dependency, image configuration, worker protocol, parser execution,
generation CLI, reports, benchmark, model, network service or provider.
This implements another small part of the approved
[evaluation](../evaluate-text-pdf-extraction/proposal.md).
