# Proposal: bounded sequential corpus run

## Why
The maintainer reviewed and merged PR #19. Verified mixed snapshots and fixed
TXT/PDF workers now need one ordered pass with the approved aggregate guards.
The parent evaluation plan was approved in PR #13; this is its next small tranche.

## What Changes
- Run only an atomically validated corpus through the fixed workers in manifest order.
- Add a validated run profile that can tighten the approved 600-second/50-MiB ceilings.
- Observe actual combined stdout/stderr bytes rather than reconstructing transport from results.
- Verify inherited offline enforcement before the first worker, including TXT-only corpora.
- Retain one immutable row per selected fixture, including unfinished work and
  completed failures; attach partial records to cancellation/cleanup exceptions.
- Repeat the bounded offline Python regressions in the existing eligible CI job.
- Preserve existing worker result APIs, the exact single process launch, runtime,
  native editor integration and eligible CI triggers.

## Capabilities
### New Capabilities
- `bounded-corpus-run`: one ordered, guarded, in-memory pass over verified synthetic snapshots.
### Modified Capabilities
None. Existing worker APIs and wire protocols remain compatible.

## Impact
Experimental Python orchestration/transport observations, independent tests and
English guides. No new dependency, image setting, workflow trigger, persisted
report, CLI, scoring, repetitions, Docling, benchmark, provider or application
feature. Persisted interruption evidence remains a subsequent reviewed tranche.
