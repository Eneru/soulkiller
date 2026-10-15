# Proposal: confined immutable run-storage foundation

## Why
PR #20 was reviewed and merged. Its ordered corpus results remain in memory.
The approved parent plan requires confined output before durable reporting;
establish that filesystem boundary as a separate small reviewable tranche.

## What Changes
- Add create-only run directories at the fixed ignored evaluation root.
- Write bounded opaque byte records with complete-frame validation and exclusive
  atomic publication; inspect known records after reopening read-only.
- Reject symlinks, existing runs/records and source/output overlap before writes.
- Preserve earlier records and incomplete scratch on interruption or I/O failure.
- Retain existing runtime/editor/CI checks; align curl-family APT patch pins
  to restore fresh builds after the hosted repository dependency conflict.

## Capabilities
### New Capabilities
- `confined-run-storage`: descriptor-anchored create-only output and bounded inspection.
### Modified Capabilities
None. The corpus runner and its result/exception contracts remain unchanged.

## Impact
Experimental Python filesystem helpers, independent tests and English guides.
No report serializer, automatic runner persistence, record catalog, CLI, scoring,
Docling, model/provider, benchmark, new workflow or application feature. The required curl-family patch-pin repair
is validated by rebuilding the existing devcontainer design.
This foundation does not complete durable comparison reporting.
