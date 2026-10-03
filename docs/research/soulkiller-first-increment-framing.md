# First persona: confirmed framing and next decisions

**Decision record:** 2026-10-03, following maintainer review and merge of
[PR #4](https://github.com/Eneru/soulkiller/pull/4).
The initial framing was reviewed and merged in [PR #6](https://github.com/Eneru/soulkiller/pull/6);
[issue #5](https://github.com/Eneru/soulkiller/issues/5) is completed. Subsequent
memory-content/deletion answers are recorded below, also on 2026-10-03.
Read the [decision register](soulkiller-decisions.md),
[report](soulkiller-feasibility-report.md) and
[evaluation proposal](soulkiller-evaluation-plan.md).

This document records confirmed intent and compares remaining options. It does
not choose a language, model, provider, storage location or implemented behavior.
Future behavior needs reviewed OpenSpec requirements, design and tasks.

## Confirmed first corpus and memory intent

- Windows on an ordinary household PC; exact hardware remains unspecified.
- TXT and PDFs containing selectable text first, in French and English.
  OCR/scanned PDFs, images, audio and video are later priorities.
- Tens to hundreds of documents, up to approximately 1,000 pages per initial
  persona: a planning profile, not a measured capacity or enforced limit.
  Total bytes, longest files, language mix and update frequency remain open.
- Compare local and remote operation before selecting either.
  This authorizes comparison, not transmission to a service or paid experiments.
- An evolving persona with memories proposed and saved automatically,
  inspectable and deletable. Saved memories are usable immediately, with their
  conversational origin preserved. They are shared across all interlocutors of
  the same persona. No manual saving/activation gate is required by these answers.
  Content is explicit interlocutor statements and faithful attributed summaries;
  no automatically inferred preferences. Deletion removes a memory and its
  derivatives while retaining history and a technical trace preventing automatic
  regeneration. Remaining operational rules below still need decisions.

French/English input priorities do not change English as the project's working
language. Cross-language retrieval, answer language and bilingual memory
summaries need separate acceptance examples.

## Local versus remote: a comparison to evaluate

For a controlled initial comparison, keeping extraction and retrieval local
would isolate inference placement as the variable. This is a proposed comparison
design, not an approved storage architecture. A remote index or remote memory
store would require its own data-flow decision.

| Criterion | Local inference on the source PC | Inference on a user-owned remote machine | Hosted inference |
| --- | --- | --- | --- |
| Proposed data path | Sources, queries, retrieved evidence and conversational context stay on the PC | Explicit request crosses a chosen transport to another owned machine | Explicit request crosses a chosen transport to a provider |
| Ordinary offline use | Possible after provisioning if every required component is local; must be tested | Depends on reachability; a LAN server differs from an Internet server | Requires the selected service and network |
| Compute placement | Generation and memory extraction use source-PC resources | These operations use the other machine; source extraction still has a local cost | These operations use provider resources; source extraction still has a local cost |
| Quality and latency | Depend on chosen model, hardware and context; unmeasured | Depend on chosen model, hardware and transport; unmeasured | Depend on chosen model, service and transport; unmeasured |
| Costs to establish | Model assets, disk, RAM, packaging, power and processing time | Server provisioning, operation and transport as well as local costs | Request/token charges, retries, memory-generation calls and service terms |
| Retention to inspect | Local transcripts, memories, indexes, caches and logs | Local state plus remote server caches and logs | Local state plus provider retention, logging and contractual controls |
| Proposed unavailable-service behavior | Explicit unavailable-model outcome; no silent remote substitution | Explicit connection/service error; retry or an approved local option | Explicit service error; retry or an approved local option |

No column is selected. Local operation is not inherently free or fast; remote
operation is not automatically better. A household-PC requirement alone does not
settle generation quality or resource use. The report supplies candidate evidence,
not runtime results for this corpus.

Before any remote trial, approve the endpoint, transmitted fields, retention and
budget. Cover questions, retrieved passages, persona profile, conversational
context and memory-generation inputs separately from complete source files.
No automatic external fallback is authorized. Provider deletion is a separate
question from deletion of a local record.

## Comparison proposal, still unexecuted

Use the same invented French/English corpus, labeled questions, provenance and
retrieval settings in each approved run. Record the chosen model and hardware;
different models make this a comparison of complete options, not a controlled
measurement of transport alone.

1. E1/E4: establish extraction and retrieval quality for the first corpus,
   including malformed TXT, broken/protected PDFs, duplicates and revisions.
   Scanned PDFs need a visible unsupported/OCR-required result in this tranche.
2. E6: compare grounded answers and automatic-memory proposals. Measure supported
   claims, citations, uncertainty, memory attribution, false memories and latency.
   Record cold/warm behavior, peak RAM, disk, request counts and total cost.
3. E7: validate native Windows startup and the selected offline/network-loss
   behavior. A successful Ubuntu devcontainer run is not a Windows result.
4. Include restart, memory inspection/deletion, stale retrieval, conflicting
   claims and imported instructions. Test expected memory sharing between two
   interlocutors of one persona separately from forbidden cross-persona leakage.

The approximately 1,000-page profile is an evaluation target, not a promise.
Small deterministic fixtures and model doubles can test contracts without paid
calls; they cannot establish real-model quality or runtime performance.
No candidate installation, fixture harness, model download or experiment is
part of this decision-recording change.

## Automatic memory: decisions still needed

Saving a conversational memory does not turn it into an original source fact.
Separate imported evidence, persona profile/style and conversation-derived
memories. These are proposed design boundaries for review.

| Question | Options or boundary to decide |
| --- | --- |
| Content (confirmed) | Explicit interlocutor statements and faithful summaries with attribution; no automatic inferred preferences. Model inventions do not become established facts |
| Attribution and access | Shared memory within the same persona is confirmed. Whose statement concerns which person, and who may access, correct or delete it? |
| Evolution | Can memories affect factual context only, or also speaking style/personality? Source identity and later experiences are distinct |
| Conflicts and correction | How to handle a memory contradicting a source or another memory? Is editing supported, or deletion and replacement? |
| History and deletion (partly confirmed) | Remove memory and its derivatives; retain history and a technical trace preventing automatic regeneration. Trace contents/lifetime, derivative boundaries, backups and remote copies still need a contract |
| Retention and budget | How much memory is retained, when is it summarized, and which compute/cost limits apply to automatic memory generation? |

Proposed future acceptance examples: saving a clearly attributed memory without
a manual approval step; inspecting its origin and timestamp; immediate use and
same-persona sharing with correct speaker attribution after restart;
correction/deletion under the chosen contract; no automatic
promotion of assistant-generated claims to source evidence; no deleted memory
reappearing within the agreed deletion scope. These are test proposals, not
demonstrated guarantees or fully approved requirements.

The deletion choice is forgetting a usable memory, not erasure of its retained
conversation. The technical trace is not an adopted database design: define
minimal metadata, handling of rephrased/duplicate memories, management rights
and the scope of any backups or remote copies before implementation.

## Next review gate

The maintainer has approved the corpus priorities and automatic memories used
immediately and shared within the same persona, with their origin preserved.
The offline/remote choice remains a comparison request. Resolve the relevant
questions above, exact hardware and cost/latency expectations, the first dialogue
presentation and delivery scope before a behavioral implementation proposal.

Completed issue #5 covered the initial decision record and comparison framing only. It does not
complete all of roadmap R1 or authorize F2-F6 experiments and implementation.
