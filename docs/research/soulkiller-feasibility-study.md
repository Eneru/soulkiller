# Study brief: local data ingestion and evidence-grounded digital personas

**Status:** topic approved in [PR #2](https://github.com/Eneru/soulkiller/pull/2);
desk research reviewed and merged in [PR #4](https://github.com/Eneru/soulkiller/pull/4),
with [issue #3](https://github.com/Eneru/soulkiller/issues/3) completed.
The [first-increment framing](soulkiller-first-increment-framing.md) records the
maintainer's subsequent corpus, comparison and automatic-memory answers.
**Study outputs:** [report](soulkiller-feasibility-report.md),
[evaluation proposal](soulkiller-evaluation-plan.md), [decisions](soulkiller-decisions.md).
**Suggested issue title:** Study local multimodal ingestion and RAG-based digital personas.
**OpenSpec preparation change:** [plan-soulkiller-feasibility-study](../../openspec/changes/plan-soulkiller-feasibility-study/proposal.md).
**Dependencies:** the reviewed development foundation. This study informs R1-R4
in the [roadmap](../roadmap.md); its work packages do not define product stages.

## Objective and confirmed direction

Identify feasible ways to simulate Soulkiller's fictional "soul capture": extract
information from a person's authorized local files, preserve usable evidence,
and support a conversation with a digital persona inspired by that person.
The output of the study is a comparison, recommendations and decisions for the
maintainer. No extraction or conversation capability exists yet.

Confirmed needs:

- Collection and extraction run on the source person's machine.
- Study text files, PDFs, images and videos, including text recognition and
  speech transcription where relevant.
- Compare technologies, libraries and languages with advantages and drawbacks.
- Evaluate RAG as the leading hypothesis. Infrastructure and maintenance concerns
  make fine-tuning a secondary option to assess, rather than the default.
- Surface unanswered questions and choices before adopting an architecture.

The input scope is explicitly selected files or folders with the data owner's
authorization. Automatic whole-machine collection is outside this brief.
Storage, indexing and inference location remain decisions to study.
A digital persona is an application behavior to evaluate, not demonstrated
consciousness digitization.

## Boundaries of this preparation

This change delivers the study brief and tracking artifacts only. It does not
run benchmarks, install candidate dependencies, create a collector, train a
model, configure a provider or execute paid LLM calls.
The study should propose any experiments with their required resources and
budget before execution. Routine evaluation must use synthetic data and require
no provider credentials. Product stages and a production stack remain open.

## Work packages for the future study

| ID | Research questions | Expected output |
| --- | --- | --- |
| W1 | Which source-machine operating systems, hardware, formats, corpus sizes and languages matter? What demonstrates a useful first conversation? | Assumption register, representative journey and maintainer question list |
| W2 | How should local selection, text extraction, OCR, transcription and visual interpretation work? How do quality and dependencies differ? | Per-format comparison and proposed extraction contract |
| W3 | How should extracted evidence be normalized, attributed, chunked, indexed, updated and deleted? | Proposed data lifecycle and retrieval comparison |
| W4 | How can a persona use facts, express style and remember conversations? Where do RAG, prompting and fine-tuning help? | Separate behavior criteria and approach comparison |
| W5 | Which language and deployment arrangements fit the constraints? Is OmniRoute useful? | Candidate architectures, language tradeoffs, resource and cost assumptions |
| W6 | Which findings support a recommendation, and which require experiments or maintainer decisions? | Ranked options, evaluation plan and decision register |

Start W1 with questions that affect scope. W2-W4 may proceed independently
against clearly labeled assumptions; W5 combines their findings. W6 must retain
unresolved decisions rather than silently choosing defaults.

### Local extraction and provenance

Compare direct text extraction with OCR for scanned PDFs and images, including
reading order, tables, handwriting and multilingual content. For video, assess
audio transcription, speaker attribution, timestamp alignment, representative
frames and visual description separately. Speech transcripts alone must not be
treated as a complete account of visual content.

Propose an extraction record with source identity, content hash, format,
language, page or timestamp reference, extractor/model version and quality
indicators where available. Distinguish extracted text from inferred descriptions
and summaries. Identify what can be retried, resumed or corrected without
reprocessing the entire corpus. Do not infer that every file on a machine is
authored by its owner or describes the same person.

### Knowledge, style and conversation memory

| Concern | Questions and observable criteria |
| --- | --- |
| Factual knowledge | Can an answer be traced to a source? How are dates, contradictions, attribution and unknown facts handled? |
| Speaking style | Which tone, vocabulary and first-person behavior are intended? How is style evaluated independently of factual accuracy? |
| Conversation memory | What persists between sessions? Who accepts, corrects or deletes a new memory? How is it distinguished from source evidence? |

Generated answers must not silently become authoritative biographical evidence.
Study subject isolation when files mention several people and when more than one
persona exists. Treat instructions inside imported documents as untrusted source
content; evaluate resistance to attempts to override conversation rules.

Compare these options against the same needs:

- A simple searchable corpus and grounded prompting as a baseline.
- RAG with lexical, vector or hybrid retrieval, optional reranking and a
  separately defined persona profile.
- Full fine-tuning and parameter-efficient adaptation, distinguishing changes
  to style or task behavior from the need for traceable, updatable facts.
- Combinations only where evidence justifies the additional complexity.

Evaluate updates, deletion, citations, uncertainty, data requirements,
training and inference resources, operating costs and maintenance for each.
Do not conclude that fine-tuning is impossible or that RAG is sufficient before
stating the hardware, model and workload assumptions.

## Initial candidates to investigate

These are research starting points, not selections or benchmark findings.
Official entry points were checked on 2026-10-01. The actual study must record
the evaluated version, license, model-weight terms and deployment dependencies.

| Area | Starting candidates or baseline | Questions to compare |
| --- | --- | --- |
| Text and document extraction | Standard text readers; [Docling](https://github.com/docling-project/docling); [Apache Tika](https://tika.apache.org/) | Encodings, document coverage, layout fidelity, local runtime and dependency footprint |
| OCR | [Tesseract](https://github.com/tesseract-ocr/tesseract); OCR integrated into document pipelines | Languages, scanned pages, handwriting limitations, CPU/GPU use and confidence handling |
| Video and audio | [FFmpeg](https://ffmpeg.org/documentation.html); [Whisper](https://github.com/openai/whisper); separate visual-model candidates to shortlist | Formats, transcription quality, frame selection, timestamps, speaker handling and processing time |
| Retrieval and storage | [SQLite FTS5](https://sqlite.org/fts5.html) as a lexical baseline; [pgvector](https://github.com/pgvector/pgvector); [Qdrant](https://qdrant.tech/documentation/) | Local packaging, embeddings, filters, hybrid retrieval, updates, deletion and operational complexity |
| RAG composition | Explicit pipeline without a framework; [LlamaIndex](https://developers.llamaindex.ai/python/framework/); [LangChain](https://docs.langchain.com/oss/python/langchain/overview); [Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/overview/) | Language fit, abstraction cost, traceability, testing and dependency burden |
| Inference and routing | [llama.cpp](https://github.com/ggml-org/llama.cpp); direct model/provider interfaces; [OmniRoute](https://github.com/NStambovsky/OmniRoute) | Hardware and model compatibility, local operation, data egress, API contracts, latency and failure handling |
| Languages and interface | Python, C#/.NET and TypeScript/Node.js; CLI, desktop and web UI options, including Angular if justified | Library access, native packaging, subprocess/API boundaries, testing, maintenance and devcontainer support |

For languages, compare a single-language implementation with a small mixed stack.
Include the cost of additional runtimes and interfaces. Compare native source
machine execution with containerized development: the current devcontainer
does not establish a deployable desktop collector.
OmniRoute evaluation must distinguish routing needs from extraction, storage and
persona behavior; compare it with direct access rather than assuming adoption.

## Comparison method and deliverables

Use one matrix with a row per candidate and these common fields: role, evaluated
version, capabilities, advantages, drawbacks, quality evidence, source fidelity,
offline operation, supported platforms, CPU/GPU/RAM/VRAM/storage, latency,
installation and packaging, license and model terms, maintenance, testability,
interoperability, cost and open questions.

Label each finding as **measured**, **documented**, **hypothesis** or **unknown**.
Cite primary sources and their access dates. Avoid scores without an explained
scale and agreed priorities. Give estimates as ranges with hardware, corpus
size, model, update frequency and conversation workload assumptions.

Deliver:

1. A report covering W1-W6, including the comparison matrix and its evidence.
2. Candidate data-flow diagrams distinguishing the source machine, storage,
   indexing, generation and UI, with any network/data-egress boundaries.
3. A reproducible evaluation proposal using synthetic fixtures and expected
   source references; document unexecuted experiments as such.
4. A decision register with options, tradeoffs, recommendation, evidence,
   uncertainty, maintainer question and effect on the next implementation.
5. A proposed smallest functional increment and follow-up issue drafts, pending
   approval and a behavior-specific OpenSpec change.

## Evaluation to design

Include plain text with varied encodings, text and scanned PDFs, images and
short videos. Propose reference facts, expected extracted content, page/timestamp
citations, known unknowns, contradictory sources and style examples.
Cover empty, corrupt, password-protected, unsupported, duplicate and oversized
inputs; low-quality scans, silent videos and transcription errors.

Separate extraction fidelity, retrieval coverage, answer faithfulness, citation
correctness, uncertainty behavior and style assessment. Define metrics,
thresholds and hardware/workload before claiming success.
Exercise interrupted processing, missing dependencies, unavailable models,
updates/deletions and isolation between subjects. Verify that source instructions
cannot change application rules. Keep fixture content synthetic.

## Maintainer decision register to open

The preparation assumed no answers. The study records confirmed Windows-first
household-PC deployment and remaining questions in the
[decision register](soulkiller-decisions.md); this table preserves the original questions.

| ID | Question | What it determines |
| --- | --- | --- |
| Q1 | Which source operating systems and CPU/RAM/GPU/storage profiles should be supported first? | Local packaging and feasible extraction/inference candidates |
| Q2 | Which file types, spoken/written languages, corpus size and update frequency are essential first? | Corpus, quality criteria and scope of the first increment |
| Q3 | Must extraction, storage, indexing and conversation all work offline? What data may leave the machine, if any? | Deployment boundaries and provider choices |
| Q4 | Should the persona speak as the person, describe them, or offer both modes? Is text chat sufficient initially? | Persona behavior, UI and whether voice is in scope |
| Q5 | How should citations, missing facts, conflicting evidence and facts about third parties appear? | Grounding, attribution and answer criteria |
| Q6 | Should conversation memories persist? Who may accept, edit or delete them? | Memory lifecycle and separation from source knowledge |
| Q7 | What import time, response latency, disk use and one-off/recurring cost limits are acceptable? | Evaluation thresholds and architecture ranking |
| Q8 | Is the first use single-user/single-persona, or must it support multiple users/personas? | Isolation, access and deployment scope |

Ask blocking questions before narrowing the study or running resource-dependent
experiments. Present nonblocking options with explicit assumptions so the
maintainer can make an informed choice.

## Acceptance criteria for the study

Checked items record desk-study deliverables, not approved technology choices or
executed experiments. See the report and decision register for limitations.

- [x] Confirmed needs, assumptions, exclusions and Q1-Q8 are recorded.
- [x] Text/PDF, image/OCR and video/audio approaches have a comparison with
      advantages, drawbacks and primary references.
- [x] RAG, prompting and fine-tuning are compared separately for facts, style
      and memory, with stated resource and maintenance assumptions.
- [x] Languages, libraries, deployment alternatives and OmniRoute have reasoned
      options without an unreviewed stack decision.
- [x] Data flow, provenance, updates, deletion and subject isolation are covered.
- [x] Synthetic evaluation covers success, boundaries and failure cases;
      measurements and unexecuted experiments are clearly distinguished.
- [x] The report ends with actionable maintainer questions, recommendations and
      a proposed first increment, all subject to human review.

## Starting the study in a new chat

Once this topic is approved, use this prompt and add any answers to Q1-Q8:

> Read AGENTS.md, README.md, openspec/config.yaml and
> docs/research/soulkiller-feasibility-study.md. Conduct the approved feasibility
> study for local multimodal ingestion and evidence-grounded digital personas.
> Write project artifacts in English. Inspect the current repository, preserve
> existing work, and run development commands only inside the devcontainer.
> Compare technologies and languages using primary sources; distinguish measured
> findings from assumptions. Ask blocking maintainer questions before dependent
> work. Deliver a study report, decision register and evaluation proposal for
> review. Prepare a separate OpenSpec change before implementing product behavior.

Record decisions and progress in the repository so the next chat can resume
without relying on the previous conversation.
