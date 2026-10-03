# Planning design

## Context

PR #6 is merged and issue #5 is completed. The maintainer explicitly authorized
two additional roadmap/issues topics and clarified memory content/deletion.
See [proposal.md](proposal.md),
[quality plan](../../../docs/development-quality.md) and
[site plan](../../../docs/documentation-site-plan.md).

## Decisions

1. Record confirmed quality/security goals as development commitments while
   distinguishing uninstalled tools and unexecuted gates. The proposed coverage
   metric is line coverage per component; exclusions and precise configurations
   belong to the reviewed implementation change.
2. Keep secret/static checks and deterministic coverage early on PRs. Use tags
   for deeper work rather than postponing basic checks. Separate compute, storage,
   runner eligibility and actual costs; no unlimited-free promise.
3. Publish only the two explicitly requested future implementation issues.
   Use Refs #7 and Refs #8 in the planning PR, because merging documentation does
   not satisfy their implementation criteria. Report native-link tooling limits.
4. Keep Docusaurus as a leading site candidate, not an adopted application
   frontend. Compare stable VitePress and document source/route/publication controls.
   Use the maintainer-reported Actions Pages setting without changing it.
5. Preserve current local devcontainer rules. A future native Windows CI lane
   requires its own reviewed tooling and execution evidence.
6. Update the memory decision register and framing with the actual answers.
   Technical deletion traces are an intent, not a selected database/algorithm.
   Their contents, correction/management rights, backups and remote copies remain
   questions; do not promise complete erasure of retained history.

## Validation and delivery

Run strict OpenSpec, whitespace, local Markdown-link/fence, scope and common
secret-pattern checks in the devcontainer. Compare LICENSE with main.
Request read-only review of quality/CI, Pages and memory wording.
Deliver a draft PR; no scanner, coverage, site build or Actions execution is
claimed for this documentation-only change.
