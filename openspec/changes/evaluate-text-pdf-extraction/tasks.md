# Tasks

The review packet was approved and merged in PR #13. Implementation is now
authorized in small reviewable tranches. [The first tranche](../implement-python-text-foundation/proposal.md)
adds runtime/checks and pure TXT evidence. [The second tranche](../implement-confined-text-corpus/proposal.md)
adds confined TXT corpus reads and literal annotations. [The third tranche](../implement-bounded-text-workers/proposal.md)
adds trusted TXT worker supervision; these foundations do not complete the parent harness.

## 1. Preparation and review packet

- [x] 1.1 Confirm PR #12 merge, preserve a clean workspace and branch from current main.
- [x] 1.2 Record plan-only scope, 8/16 GiB CPU-only profiles and the initial local-manager choice.
- [x] 1.3 Check primary metadata/source for the proposed native, model-free candidates.
- [x] 1.4 Prepare proposal, experimental behavior delta, design and staged rollout.
- [x] 1.5 Validate strict OpenSpec, changed documentation/configuration and publication scope.
- [x] 1.6 Obtain maintainer review of the candidate scope, resource guards and contract.

## 2. Implementation after plan review

- [ ] 2.1 Provision an isolated pinned Python/candidate/check environment in the devcontainer; inventory artifacts, licenses and advisories.
- [ ] 2.2 Construct/hash the independent bilingual fixtures and annotations; review their source/expected-data independence.
- [ ] 2.3 Implement explicit manifest validation, immutable-source handling and resolvable TXT/page evidence.
- [ ] 2.4 Implement native adapters, isolated resource-bounded workers, cancellation and per-file failures without models or networking.
- [ ] 2.5 Implement comparison scoring, qualified raw metrics and bounded inspectable reports.
- [ ] 2.6 Add independent unit/integration/CLI boundary tests, all-source line coverage >=70%, Bandit and applicable lint/type/dependency gates.
- [ ] 2.7 Document container CLI/hooks/editor checks and extend existing canonical PR-to-main/SemVer-tag CI only.
- [ ] 2.8 Build/start the updated container; verify clean-cache offline candidate smoke tests, writes/persistence, failure containment and LICENSE preservation.
- [ ] 2.9 Run the reviewed bounded Linux comparison and publish actual results/errors, without a Windows performance claim.
- [ ] 2.10 Deliver the tested implementation/results in a ready PR using the verified App bot; request human review/manual merge.

## 3. Separate follow-ups

- [ ] 3.1 Review native Windows lane and remaining CPU/OS/storage profile before E7.
- [ ] 3.2 Decide whether learned-layout Docling assets or larger corpus trials are justified by native findings.
- [ ] 3.3 Propose retrieval and local/remote inference comparisons with their own contracts, data boundary and resource budget.
