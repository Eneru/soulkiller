# Tasks

## 1. Contract and bounded protocol

- [x] 1.1 Implement immutable limits/results and safe input validation; verify invalid types, limits and byte boundaries with independent unit tests.
- [x] 1.2 Implement strict bounded response encoding/validation; verify duplicate keys, non-finite values, schema/types, hash mismatch and outcome/text consistency.
- [x] 1.3 Document the byte API, defaults and named errors; verify examples against the implemented public exports.

## 2. Trusted worker and supervision

- [x] 2.1 Implement the fixed isolated bootstrap with verified early Linux address-space enforcement; verify real UTF-8 success/empty/invalid cases and unavailable-enforcement tests.
- [x] 2.2 Implement one-deadline nonblocking input/output transfer; verify stalled input, timeout, exact output boundary and both-stream overflow tests.
- [x] 2.3 Implement process-group termination and bounded leader reaping on every exit; verify cancellation, inherited pipes and distinct safe cleanup failure tests.
- [x] 2.4 Document process/network boundaries and deferred PDF/runner work; verify the guide matches observed behavior without sandbox or benchmark claims.

## 3. Integration and delivery

- [x] 3.1 Run canonical static, unit/process, coverage and security checks inside the devcontainer; verify all maintained worker source is included and executable line coverage is at least 70%.
- [x] 3.2 Exercise the real worker in a network-disabled container with approved resource caps and only the Soulkiller mount; record the actual launch and outcomes.
- [x] 3.3 Update README, CHANGELOG and parent progress; verify internal links and keep unfinished evaluation tasks unmarked.
- [x] 3.4 Run strict OpenSpec validation and git diff --check; verify LICENSE and CI triggers remain unchanged.
- [x] 3.5 Prepare the exact staged tree, Conventional Commit metadata and ready-PR inputs; run publication preflight. Record live publication/signature/tree verification in the delivery PR.
- [ ] 3.6 Obtain maintainer review and confirm manual merge before reporting this tranche complete.
