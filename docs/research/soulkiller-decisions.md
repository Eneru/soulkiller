# Soulkiller decisions and proposed next increment

**Status:** study reviewed and merged in PR #4; maintainer answers updated 2026-10-03.
Options beyond the confirmed answers remain proposals.
No technology or product behavior is adopted by this register.
Read the [report](soulkiller-feasibility-report.md),
[evaluation proposal](soulkiller-evaluation-plan.md) and
[approved brief](soulkiller-feasibility-study.md).
Study: completed [issue #3](https://github.com/Eneru/soulkiller/issues/3).
Current framing: [issue #5](https://github.com/Eneru/soulkiller/issues/5) and the
[first-increment decision record](soulkiller-first-increment-framing.md).

## Maintainer answers and open assumptions

| Brief ID | Current answer / status | Consequence |
| --- | --- | --- |
| Q1 | Confirmed: Windows first, ordinary household PC. Exact Windows version/architecture, CPU/RAM/storage remain open. No dedicated GPU is a working baseline assumption | Do not require WSL/Docker or a developer SDK on the source PC without a separate decision; measure native packaging/CPU costs |
| Q2 | Confirmed: TXT and born-digital PDF first, French/English; tens to hundreds of documents, up to approximately 1,000 pages. Total bytes, longest files, language mix and update frequency remain open | Use this planning corpus; no tested capacity or hard limit. OCR, images, audio/video follow later; cross-language retrieval and answer language remain to specify |
| Q3 | Confirmed request: compare local and remote before deciding. Required offline behavior, allowed transmitted fields/endpoints and retention remain open | Compare options and plan measurements; no data egress, paid trial or remote placement is authorized |
| Q4 | First-person versus descriptive mode, text/voice and citation presentation unanswered | Propose text dialogue with inspectable sources; voice/avatar remain separate scope choices |
| Q5 | Missing/conflicting facts and third-party attribution behavior unanswered | Propose explicit uncertainty, source dates and author/subject distinctions |
| Q6 | Confirmed: evolving persona; automatic, inspectable/deletable memories used immediately with conversational origin preserved and shared by all interlocutors of the same persona. Content, attribution/access, style changes, correction, retention and deletion scope remain open | Preserve automatic saving/use and intentional same-persona sharing; do not impose manual approval. Keep conversational memories distinct from source evidence and separate personas |
| Q7 | Latency, import time, disk and financial limits unanswered; clarification requested | No numeric feasibility promise or provider quotation; approve profiles/gates before experiments |
| Q8 | Same-persona memories shared across interlocutors confirmed; user/persona counts, authentication and access/management rights remain open | Test intended same-persona sharing separately from cross-persona isolation; no deployment or access model is adopted |

An unanswered question is not consent or a chosen default. Exact RAM and
acceptable latency should become observable requirements in the next approved
OpenSpec change. Optional illustrative test tiers could compare 8 and 16 GiB
CPU-only PCs, but neither tier is a confirmed minimum or performance guarantee.

## Choices for review

| ID | Options and tradeoff | Recommendation / evidence status | Decision needed before |
| --- | --- | --- | --- |
| D1 Data boundary | All local: more on-PC compute; owned remote inference: separate machine/transport; hosted inference: external data handling and cost | Maintainer requests comparison before selection; see the framing document. No endpoint or data path approved | Real-model experiments or any data egress |
| D2 Principal language | Python: extraction ecosystem; C#/.NET: Windows application/packaging; TypeScript: UI/model-adapter fit | Python is preferred extraction benchmark candidate; C# alternative if Windows integration dominates. No productivity benchmark | Adding runtime/dependencies and production code |
| D3 Document pipeline | Small text/pypdf path; Docling structured path; Tika broad formats; PyMuPDF with distribution review | Benchmark simple versus structured on the agreed corpus; add conditional tools only for a needed format | Extraction contract and package inventory |
| D4 Retrieval store | SQLite lexical baseline; dense/hybrid; pgvector with PostgreSQL; Qdrant dedicated service | Establish the lexical reference, then measure semantic gains. Service choice follows scale/shared-data requirements | Storage/embedding dependency adoption |
| D5 Persona method | Grounded prompting/RAG; full tuning; PEFT; combinations | RAG plus approved profile first; tuning only for a measured unresolved style/behavior gap | Persona prompt/answer policy and any training |
| D6 Style, facts and memory | Automatic memories, immediate use with origin and same-persona sharing confirmed; content, attribution/access, conflicts and deletion semantics open; citations open | Keep source evidence, profile/style and conversational memories distinct; preserve shared-memory scope and inspectability/deletion intent | End-to-end conversation and memory behavior |
| D7 Inference/routing | llama.cpp; Ollama; explicit hosted adapter; optional OmniRoute | One explicit endpoint first. Gateway only if routing benefit and eligible data paths are approved | Provider/model selection or service integration |
| D8 User experience and delivery | CLI/file picker; desktop/web; persistent service; UI framework | Visible explicit import with progress/cancellation; postpone framework/service choice | UI scope and Windows deployment tests |
| D9 Benchmarks | Minimal synthetic corpus or broader multimodal tranche; local only or approved external comparison | Approve small E1/E4/E6/E7 tranche according to Q2/Q3/Q7; include OCR/media only if first-priority needs require them | Resource-dependent experiment execution |

The [report](soulkiller-feasibility-report.md) supplies primary evidence and
limitations for each candidate. Recommendations are engineering hypotheses;
neither a permissive code license nor an upstream benchmark establishes adoption.

## Candidate first functional increment

This is a proposal for approval, not named Soulkiller stages or implemented work.

**User outcome:** the user explicitly selects a small synthetic TXT/born-digital
PDF collection in French/English on Windows, inspects attributed passages,
asks a question of one persona and receives a grounded answer with source references or uncertainty.

**Proposed scope:**

- Explicit selection/import, bounded processing and visible per-file outcomes.
- Evidence records with subject/source/revision and page/offset citations.
- Local lexical index and an approved persona profile; one model adapter.
- No automatic collection, background startup or paid-provider requirement.
- Automatic persistent memories are usable immediately and shared within the
  same persona, with conversational origin preserved. Specify content, attribution,
  access/management and deletion rules before implementing them.
- OCR, image descriptions, video, dense retrieval and gateway integration are
  follow-ups unless Q2 makes one necessary for the first useful journey.

**Proposed acceptance:** actual native Windows run on an approved household-PC
profile; no source-machine developer setup required under the agreed packaging;
correct annotated source references, explicit unknown/conflict handling,
cancellation/restart and update/deletion behavior; deterministic tests in the
devcontainer with synthetic fixtures and model doubles; separate opt-in real-model
quality/runtime evaluation. Exact quality/performance gates require approval.

Before code: settle D1/D2/D5/D6/D8 and the necessary Q answers, write the proposal,
behavior specifications, design and tasks, then request review of that concrete
increment. The desk study's approval does not adopt this scope automatically.

## Follow-up issue drafts

Issue #3 is completed. Issue #5 records the first answers and comparison framing,
contributing to F1/R1 without completing their full scope. F1-F6 below remain
proposals requiring review before publication or implementation.

| Local ID / proposed title | Goal | Dependencies | Acceptance criteria |
| --- | --- | --- | --- |
| F1 — Define the Windows persona journey and data boundary | Resolve Q1-Q8/D1/D6/D8 for a useful first conversation | Study review; roadmap R1 | Target profile, corpus, answer/memory behavior, data flow and exclusions approved in OpenSpec |
| F2 — Evaluate extraction and retrieval on a synthetic corpus | Resolve E1/E4 plus conditional OCR/media needs | F1; budget/runtime approval | Pinned artifacts/fixtures, primary license inventory, reproducible commands, quality/resource results and failure records; no paid routine calls |
| F3 — Validate native Windows delivery | Establish source-machine packaging and execution evidence | F1; principal-language choice; approved Windows test lane | Bundle with native/model dependencies, install/start/import/cancel/restart/offline/Unicode-path checks on declared Windows profile; no claim from Linux tests alone |
| F4 — Specify and deliver the first grounded conversation | Implement the approved narrow journey | F1, F2, F3; roadmap R2/R3 | Reviewed behavior specs, tests for success/errors/boundaries, one endpoint, evidence citations and uncertainty, docs and draft PR |
| F5 — Evaluate richer media and semantic retrieval | Add capabilities when justified by quality/coverage | F2/F4 and explicit priorities | Per-format/retrieval baseline comparison, resources/lifecycle/provenance tested before adoption |
| F6 — Evaluate optional routing or style adaptation | Resolve a demonstrated multi-endpoint or style gap | F4; approved data boundary/budget; roadmap R4 as applicable | Direct versus gateway or prompt versus PEFT evidence; no automatic external fallback, explicit decision and separate change |

These map onto R1-R5 rather than replacing the roadmap with invented product
stages. Publication, technology adoption and implementation remain separate
review decisions.

## Handoff to the next chat

Include any maintainer decisions as D-ID/Q-ID answers in this document before
starting implementation. Use this prompt once an increment is approved:

> Read AGENTS.md, README.md, openspec/config.yaml, the feasibility report,
> evaluation plan, decision register and first-increment framing under
> docs/research/. Inspect Git state
> and the relevant issue/PR. Prepare an OpenSpec change for the explicitly
> approved first increment, preserving the confirmed Windows target and data
> boundary. Keep facts, style and conversation state separate. Write all project
> artifacts in English. Ask about blocking unresolved decisions before dependent
> work. Run development commands inside the devcontainer. Do not adopt unapproved
> technologies, run paid calls or merge a PR.

The study report is reviewed and merged. Confirmed corpus and automatic-memory
intent do not settle the open product choices, native Windows validation or
E1-E9 measurements. Review of the new decision record remains pending.
