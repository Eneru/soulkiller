# Proposed roadmap

R0 is tracked in [issue #3](https://github.com/Eneru/soulkiller/issues/3) after
maintainer approval. The remaining entries are **issue drafts** for review.
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
analyze-soulkiller-feasibility. Desk research is prepared for review; experiments
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
- [ ] Storage and contracts required by the journey specified.
- [ ] Tools and versions added to the devcontainer; local startup documented and verified.

## R3 — Establish a reproducible testing strategy

**Goal:** make the first journey and its failure cases testable from the devcontainer.

**Dependencies:** R1 and R2.

**Deliverables and acceptance criteria:**

- [ ] Responsibilities of unit, integration and end-to-end tests defined.
- [ ] Deterministic LLM test doubles, synthetic fixtures and test isolation defined.
- [ ] Reproducible test command requiring no external provider or LLM spending.
- [ ] Explicit decision on Docker-in-Docker; add it only if justified.
- [ ] Optional minimal CI proposal with an estimate of GitHub Actions usage.

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
- [ ] Usage documentation and CHANGELOG updated.
- [ ] PR includes test results and is merged only after human review.
