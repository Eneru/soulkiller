# Proposed roadmap

R0 is completed in [issue #3](https://github.com/Eneru/soulkiller/issues/3) after
maintainer review and merge of PR #4. [Issue #5](https://github.com/Eneru/soulkiller/issues/5)
is completed by reviewed PR #6 and records initial R1/F1 framing only.
The maintainer authorized [issue #7](https://github.com/Eneru/soulkiller/issues/7)
for quality/security and [issue #8](https://github.com/Eneru/soulkiller/issues/8)
for the documentation site. The GitHub App publication tranche starts R6 with
tooling tests and native quality checks; the documentation site remains planned. R1-R5 remain
**issue drafts** for review. R6 accompanies development from the first component;
its numbering does not defer security until after R5.
No issues are created automatically. After approval, publish them in English
and replace their local identifiers with GitHub links. The order below expresses
dependencies; it does not define the product stages.

## R0 / Issue #3 — Study local ingestion and digital personas

**Goal:** evaluate how authorized local text/PDF, image and video data could
support an evidence-grounded conversation with a digital persona.

**Dependencies:** the reviewed development foundation. This study informs R1-R4
and collects the product questions needed before architecture selection.

**Issue topic:** [complete study brief](research/soulkiller-feasibility-study.md),
including candidate references, work packages W1-W6, decisions Q1-Q8 and a
new-chat prompt. Preparation change: plan-soulkiller-feasibility-study.

**Study delivery:** [report](research/soulkiller-feasibility-report.md),
[evaluation proposal](research/soulkiller-evaluation-plan.md) and
[decision register](research/soulkiller-decisions.md). Study change:
analyze-soulkiller-feasibility. Desk research is reviewed and merged; experiments
and technology adoption remain pending. Follow-up issue drafts are in the register.

**Deliverables and acceptance criteria:**

- [x] Extraction, RAG/fine-tuning and language/library alternatives compared
      with advantages, drawbacks, primary references and declared assumptions.
- [x] Facts, speaking style and conversation memory assessed separately.
- [x] Candidate architectures, provenance and data lifecycle documented.
- [x] Hardware/cost assumptions and synthetic evaluation proposal provided.
- [x] Maintainer questions, recommendations and a first increment proposed
      for review; no unreviewed stack adoption.

## R1 — Define the stages and first user journey

Initial decisions: [first-increment framing](research/soulkiller-first-increment-framing.md).
TXT/PDF text, French/English, a small planning corpus and automatic memories
with immediate use, preserved origin and same-persona sharing are confirmed. First-person text dialogue with consultable sources is also confirmed. Offline placement, detailed memory and journey rules remain open.
Explicit uncertainty, sourced contradictions without automatic resolution and
inspectable/deletable speaking-style changes are now confirmed. The
[behavior packet](research/soulkiller-behavior-framing.md) compares access options
and proposes acceptance examples. The first increment now selects one local
manager with unauthenticated interlocutor labels. The evaluation target is
8 GiB RAM CPU-only, with 16 GiB for comparison; exact CPU/OS/storage and
performance remain open. These decisions
do not complete the criteria below.

**Goal:** establish what Soulkiller should do, for whom, with which input data
and observable outcomes. Distinguish the fictional inspiration from the actual
capabilities being pursued.

**Dependencies:** the reviewed development foundation and R0 findings.

**Deliverables and acceptance criteria:**

- [ ] Audience, problem, first journey and exclusions approved by the maintainer.
- [ ] Stages named and described, including inputs, outputs and transition conditions.
- [ ] Storage, privacy, consent and data deletion needs defined.
- [ ] Synthetic examples and observable criteria documented in an OpenSpec change.

## R2 — Choose the architecture and languages

**Goal:** choose the smallest architecture that supports the first journey.

**Dependencies:** R1.

**Deliverables and acceptance criteria:**

- [ ] Component responsibilities and interactions defined.
- [ ] Reasoned decision on Python, .NET and any frontend; no stack imposed in advance.
- [ ] Applicable quality/security/coverage gates planned with each introduced component (R6 / issue #7).
- [ ] Storage and contracts required by the journey specified.
- [ ] Tools and versions added to the devcontainer; local startup documented and verified.

A proposed first experimental tranche is
[evaluate-text-pdf-extraction](../openspec/changes/evaluate-text-pdf-extraction/proposal.md):
a synthetic native TXT/PDF comparison, not application-language adoption.
Its proposal, experimental contract, design and tasks are prepared for review
only. No candidate/harness or R2 acceptance criterion is completed by this packet.

## R3 — Establish a reproducible testing strategy

**Goal:** make the first journey and its failure cases testable from the devcontainer.

**Dependencies:** R1 and R2.

**Deliverables and acceptance criteria:**

- [ ] Responsibilities of unit, integration and end-to-end tests defined.
- [ ] Minimum 70% coverage, metric/exclusions and scanner failure policy defined under the [quality plan](development-quality.md).
- [ ] Deterministic LLM test doubles, synthetic fixtures and test isolation defined.
- [ ] Reproducible test command requiring no external provider or LLM spending.
- [ ] Benchmarks and bounded load-test profiles, hardware/corpus baselines,
      metrics and agreed thresholds; distinguish fast regression checks from deeper runs.
- [ ] Explicit decision on Docker-in-Docker; add it only if justified.
- [ ] Bounded GitHub Actions gates designed with early PR checks and deeper version-tag checks; issue #7 tracks implementation alongside components.

## R4 — Evaluate OmniRoute and LLM access

**Goal:** decide whether [OmniRoute](https://github.com/NStambovsky/OmniRoute)
fits the identified needs.

**Dependencies:** R1 and R2; reproducible trials build on R3.

**Deliverables and acceptance criteria:**

- [ ] Evaluated version, license and verified interface compatibility documented.
- [ ] Comparison with direct provider access and adoption criteria.
- [ ] Latency, usage and cost measurements for a representative scenario.
- [ ] Errors, rate limits, timeouts, retries and provider failover evaluated.
- [ ] Data flows, logs, secret storage and privacy rules reviewed.
- [ ] Adoption or rejection decision reviewed; no secrets or automatic paid calls.
- [ ] If adopted: optional local service, configuration and test procedure documented.

## R5 — Deliver the first functional increment

**Goal:** implement one complete slice of the journey selected in R1.

**Dependencies:** R1, R2, R3 and the R4 decision if the journey uses LLMs.

**Deliverables and acceptance criteria:**

- [ ] OpenSpec proposal, specifications, design and tasks reviewed.
- [ ] Journey runnable entirely from the devcontainer.
- [ ] Success cases, invalid data and dependency unavailability tested.
- [ ] Applicable local/Actions coverage and security gates delivered with the increment (R6 / issue #7).
- [ ] Usage documentation and CHANGELOG updated.
- [ ] PR includes test results and is merged only after human review.

## R6 / Issue #7 — Quality and security from each component's first delivery

**Goal:** make tests, security analysis and automation native to development,
rather than a later retrofit. See the [quality plan](development-quality.md).

**Dependencies:** reviewed foundation; extend alongside each adopted language,
Docker change and runnable web component. Accompanies R2/R3/R5 and R7.

**Deliverables and acceptance criteria:**

- [ ] Local/Actions entrypoints and pinned versions added with the relevant component.
- [ ] Minimum 70% coverage with reviewed metric/exclusions and meaningful tests.
- [ ] Gitleaks, Hadolint and appropriate language analysis; Bandit if Python.
- [ ] Repository-local Gitleaks pre-commit hooks and container-side editor
      diagnostics, including Hadolint with its image-installed binary; explicit CLI/CI execution.
- [ ] Synthetic benchmark/load-test commands and bounded PR versus version-tag
      lanes when measurable components exist; no performance claims without evidence.
- [ ] Web ZAP against an ephemeral synthetic instance once applicable.
- [ ] Fast PR gates plus bounded deeper version-tag scans, safe tokens/permissions,
      redacted reports and declared runner/storage budget.
- [ ] Actual results, intentional skips and limits documented; manual review.

## R7 / Issue #8 — Publish readable documentation through Pages Actions

**Goal:** create an accessible, distinctive static English documentation site,
with repository Markdown/OpenSpec as the authoritative source.
See the [site plan](documentation-site-plan.md).

**Dependencies:** reviewed generator/visual/source proposal, applicable R6 gates,
and the maintainer-reported Pages Actions setting. No application stage depends
on choosing the site's frontend framework.

**Deliverables and acceptance criteria:**

- [ ] Docusaurus/stable VitePress comparison resolved in a reviewed implementation proposal.
- [ ] Responsive, keyboard-usable visual design and clear accepted/draft status.
- [ ] Explicit public-source selection, compatible rendering and correct links/assets.
- [ ] Devcontainer production build/preview and applicable tests/checks.
- [ ] Unprivileged PR build, isolated artifact deployment from reviewed SemVer version tag;
      no branch deployment, custom PAT or settings changes.
- [ ] Deployment evidence, bounded Actions usage and maintenance instructions.

Issue #7 receives its first tooling tranche in `configure-github-app-publication`:
[publication CLI](github-app-publication.md), [quality commands](quality-checks.md),
70% publisher line-coverage gate and bounded PR-to-main/version-tag Actions. Broader component
gates, web DAST and product benchmarks remain open; this PR uses Refs #7.
Issue #8 is published but its site implementation has not started.

## Extraction implementation tranches

The approved PR #13 plan is being implemented in short reviewed PRs.
[Tranche 1](../experiments/text-pdf/README.md) supplies Python/checks and pure TXT
evidence only. Next: confined manifest/corpus reads; bounded pypdf workers;
native Docling/scoring/reports; then the approved offline Linux comparison.
Each requires independent tests and review; no E1 result, production-stack
choice, Windows benchmark, provider or memory implementation is implied.
These subdivisions are documented here rather than published via the human
connector: the App publication tool has no Issues/subissue or native Development
branch-link operation. R1-R5/F1-F6 proposals remain subject to their review rule.
