# Proposal: supervised native PDF worker

## Why
The maintainer reviewed and merged PR #18. The approved extraction evaluation
now has verified PDF snapshots and a native adapter, but parsing still needs
early guards, bounded process supervision and independent response validation.

## What Changes
- Add a fixed native-PDF byte worker with source/page bounds, existing validated
  resource limits and immutable typed results.
- Verify the externally supplied offline Linux network namespace and establish
  address-space limits before candidate/package imports.
- Reuse the sole reviewed process-launch/lifecycle implementation through an
  explicit typed completion collaborator; preserve TXT API and wire semantics.
- Add a separate strict PDF response protocol with source/page/outcome invariants.
- Exercise real workers in a bounded network-disabled container and preserve
  existing runtime/editor/security/coverage integration.

## Capabilities
### New Capabilities
- `supervised-pdf-worker`: guarded native parsing, verified PDF responses and
  mandatory lifecycle cleanup for the synthetic evaluation.
### Modified Capabilities
None. TXT results/protocol and corpus reference metadata remain unchanged.

## Impact
Experimental Python worker/protocol modules, independent tests and English
guides. No dependency, image privilege, workflow trigger, ingestion CLI,
whole-run scheduler, persistence, scoring, Docling, benchmark or application
feature is added. Continue the approved
[evaluation](../evaluate-text-pdf-extraction/proposal.md) in reviewed tranches.
