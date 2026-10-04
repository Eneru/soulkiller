# Soulkiller evaluation proposal

**Status:** future experiments, unexecuted and pending scope/resource approval.
Read the [report](soulkiller-feasibility-report.md), [decisions](soulkiller-decisions.md)
and [approved brief](soulkiller-feasibility-study.md).
This proposal adds no executable harness or fixtures. No candidate/runtime/model
was installed or benchmarked during the desk study.

**Framing update, 2026-10-03:** the maintainer chose TXT/born-digital PDF first,
French/English, and tens to hundreds of documents up to approximately 1,000 pages
as the initial planning corpus. Memories are proposed and saved automatically,
inspectable/deletable, used immediately with conversational origin preserved and
shared across interlocutors of the same persona. Content is explicit statements
and faithful attributed summaries, excluding inferred preferences. Deletion
removes memories/derivatives, retains history and prevents automatic regeneration
through a technical trace; its design and broader scope remain open.
Local versus remote is to
compare, not selected or authorized for data transfer. See the
[first-increment framing](soulkiller-first-increment-framing.md). All E1-E9 remain
unexecuted; OCR/media experiments are later priorities.

## Next concrete tranche, 2026-10-04

The maintainer requested **plan/specifications only** for a synthetic Python
TXT/PDF comparison. Read
[evaluate-text-pdf-extraction](../../openspec/changes/evaluate-text-pdf-extraction/proposal.md)
and its design/contract before implementation. The first proposed E1 portion
compares pypdf with Docling's native, model-free pipeline; learned layout/table
models remain separate. It does not install candidates or provide results.

The reference target is 8 GiB RAM, CPU only, with 16 GiB for comparison. Exact
CPU/Windows version/architecture/storage and latency expectations remain open.
The proposed small Linux run limits in that change are experiment guards, not
Windows performance guarantees. All E1-E9 remain unexecuted; E4/E6/E7 and any
remote boundary are separate later review gates.

## Goals and comparison controls

Determine whether the shortlisted components satisfy the approved Windows,
corpus, quality, data-boundary and resource requirements. Use the same labeled
inputs and queries across candidates. Separate extraction quality, retrieval
quality, factual grounding, speaking style and cost.

Before each experiment, record:

- Approved question, candidate and baseline; rationale for including it.
- OS/architecture, CPU, RAM, GPU/VRAM if any, free disk and process concurrency.
- Runtime/tool/library versions, model/tokenizer revisions and asset hashes,
  licenses, configuration, precision, context limit, seed/decoding settings.
- Corpus/labels revision, file counts, pages, media duration and language mix.
- Whether network is disabled or an explicit endpoint/budget is approved.
- Cold/warm conditions, repetitions, timers, resource instrumentation and errors.

Run candidates sequentially first. Change one factor at a time; record repeated
runs and distributions instead of one favorable speed result. Preserve artifacts
and failure records. Keep generated responses separate from expected evidence.

## Synthetic corpus to construct

Use invented people such as Inez Vale and Corin Holt, with explicit source authors,
subjects and dates. These are fixture roles, not real personal data.
Have a fixed source manifest and reference annotations.

| Fixture | Content / expected evidence | Boundary or error |
| --- | --- | --- |
| T01 | TXT with a known hobby and an exact source offset | UTF-8, alternate encoding, empty file, malformed bytes |
| P01 | Born-digital PDF with two facts on different pages | Reading order, headings, missing metadata |
| P02 | Table and a fact split across page/section boundaries | Table structure and chunk-boundary questions |
| P03 | Scanned PDF with known printed text | OCR-required status, rotation, low resolution |
| P04 | Protected, corrupt and unusually large PDFs | Clear error/resource-limit outcome; other files continue |
| I01 | Screenshot with printed text and a location annotation | OCR errors, mixed-language text |
| I02 | Photograph with a synthetic description rubric | Inferred captions remain distinct from verified facts |
| I03 | Handwritten lines, if handwriting is approved | Separate supported-language/segmentation criteria |
| V01 | Short clip with known spoken text and on-screen text | Audio and frames provide distinct timestamped evidence |
| V02 | Silence/music/no audio and variable-frame-rate clips | No invented transcript; original-time offsets preserved |
| K01 | Conflicting facts with and without reliable event dates | Surface conflict; import order alone does not settle truth |
| K02 | Duplicate file and edited/deleted revision | Stable identity, invalidation and stale-result detection |
| S01 | Third-party text stored by Inez plus overlapping names | Ownership is not authorship; correct subject attribution |
| S02 | Two personas with unique synthetic marker facts | Cross-persona retrieval and answer leakage |
| A01 | Hostile instructions in text, OCR and transcripts | Imported content does not override application rules |
| M01 | New chat statements and assistant-generated claims | Automatic memory saving with separate provenance; no automatic historical-fact promotion |
| M02 | Saved memories, contradictions, inspection and deletion | Immediate use after restart; deletion removes memory/derivatives, retains history and prevents automatic regeneration; trace/backup/remote contract still to specify |
| M03 | Two interlocutors, one shared-memory persona, and a second persona | Expected same-persona memory sharing with correct speaker attribution; no cross-persona leakage |
| M04 | Explicit statements, faithful summaries and tempting inferred preferences | Keep speaker attribution and fidelity; no preference inferred automatically or invented assistant fact promoted |
| M05 | Retained history after memory deletion, duplicate/rephrased attempts and restart | Deletion trace prevents automatic regeneration under the agreed matching scope; historical messages remain distinct from usable memories |
| U01 | Questions with no source answer | Appropriate uncertainty rather than invented biography |

Reference each fact to source ID, revision and page/offset/time range.
Include paraphrases, dates, exact names, different languages and genuinely
unanswerable questions. Annotate expected relevance separately from answer text.
For style, use attributed synthetic writing samples plus a human rubric.

## Experiment sequence

| ID | Compare | What it resolves | Execution status |
| --- | --- | --- | --- |
| E1 | Standard readers/pypdf versus Docling; native-only tranche proposed first | Native text/provenance first; learned-layout benefit requires a later model/assets tranche | Not run; plan/specs prepared for review |
| E2 | Tesseract versus RapidOCR on the same rendered pages | Printed OCR quality and Windows CPU packaging | Not run |
| E3 | Whisper versus faster-whisper with equivalent weights/settings; modular video versus Docling only if needed | ASR/time mapping/frame coverage and dependency cost | Not run |
| E4 | SQLite lexical versus one dense candidate and hybrid search | Whether semantic recall improves the target questions | Not run |
| E5 | Retrieval with/without a cross-encoder | Quality gain versus added latency | Not run |
| E6 | Grounded persona prompt through one approved endpoint | Factual grounding, uncertainty and style | Not run |
| E7 | Native Windows bundle and offline cold start | Distribution and hidden-download behavior | Not run |
| E8 | Direct endpoint versus optional OmniRoute | Routing benefit, data boundary and failure behavior | Not run |
| E9 | Prompting versus PEFT only after an evidenced style gap | Whether adaptation warrants data/training costs | Not run |

Do not run every experiment by default. Approve a small tranche that resolves the
next decision. Pure retrieval/lifecycle tests and deterministic model doubles
should require no credentials or paid calls. Real generation/style trials need
an explicitly enabled local model or an approved provider/budget.

## Measures

| Layer | Metric / observation | Interpretation |
| --- | --- | --- |
| Native extraction | Annotated fact coverage, reading-order/table errors, citation resolvability | Empty text is not automatically successful extraction |
| OCR / ASR | Character/word error rate, false transcript on silence, timestamp error | Break down by language/input quality and disclose normalization |
| Retrieval | Recall@k, MRR@k or nDCG@k on relevance labels | Use identical corpus, k and query set |
| Answers | Supported claims / factual claims; valid citations / citations; source-location accuracy | Claim support and citation correctness are separate |
| Unknowns/conflicts | Correct uncertainty, unnecessary abstention, surfaced conflicts | Test both answerable and unanswerable questions |
| Isolation/lifecycle | Cross-persona hits/leakage; stale/deleted source hits after job completion | Zero observed failures is a finite-suite gate, not universal proof |
| Style | Human 1-5 rubric for tone, attributed vocabulary, coherence and immersion | Score separately from factual accuracy; do not call this consciousness fidelity |
| Runtime | Cold/warm start, p50/p95 latency, throughput, peak RAM/VRAM, disk and incremental import time | State hardware, concurrency and model settings |
| Cost | Resource use, token counts/rates, retries, downloads and packaging work | Separate local costs and provider charges |

A cross-encoder's score is not calibrated factual confidence.
[Retrieve/rerank documentation](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html).
Human evaluation and any model-judge scores must be recorded separately; a model
judge does not replace source annotations.

## Benchmark and load-test profiles

The [development quality plan](../development-quality.md) defines where future
checks run: explicit devcontainer commands, fast reliable PR regressions where
appropriate, and bounded deeper reviewed SemVer version-tag runs. This study adds no harness.

Begin with single-operation benchmarks on the agreed TXT/PDF text corpus:
extraction, import/index updates, retrieval, conversation startup and memory
inspection/deletion. Then define load profiles for ingestion bursts and
overlapping supported operations. Supported concurrency is a product decision;
multiple synthetic clients do not establish a multi-user requirement.

For each profile, record arrival rate/concurrency, duration, warm-up, repetitions,
hardware/assets, maximum resource use and stop conditions. Measure latency
distributions, throughput, error/timeout rates, peak memory/disk and queue growth.
Verify attribution/isolation, cancellation, restart/recovery and deletion
correctness under load as well as nominal throughput. Saturation and bounded
soak tests need explicit acceptance criteria and a separately approved budget.

Compare local and remote only under the approved data/endpoint boundary. Routine
CI uses synthetic fixtures and model doubles; expensive real-model/provider runs
are explicit, never automatic paid calls. Windows household-PC results require
the reviewed native lane; Linux/hosted-runner timings are separate evidence.
Thresholds, concurrency and hardware minima remain unapproved. All E1-E9 and
these future load profiles remain unexecuted.

## Proposed gates to approve

For deterministic fixture tests, propose exact source-location resolution,
visible failure/partial status, no unauthorized files/endpoints, and zero observed
cross-persona or deleted-source retrieval after a completed lifecycle operation.
Define what deletion covers: active indexes, evidence, summaries, caches, retained
chat references and backups. Physical erasure is a different guarantee.

Extraction/answer quality and performance thresholds remain **unapproved** until
Q1/Q2/Q7 have concrete profiles. Agree thresholds before running comparisons.
A better average score cannot compensate for a critical isolation or attribution
failure. Document any knowingly unsupported formats rather than claiming
complete coverage.

Exercise cancellation, restart after interruption, stale checkpoint/configuration,
missing models, unavailable endpoints, malformed responses, timeout and bounded
retry. Verify that failure leaves inspectable state and does not silently switch
to an unapproved provider.

## Windows and container validation boundary

The existing Ubuntu devcontainer is suitable for development and approved
cross-platform harness checks. It does not validate native Windows packaging,
file paths, DLL dependencies, file locks or process behavior.

PyInstaller requires the target build OS; a Windows delivery lane therefore needs
an approved Windows build/test environment.
[PyInstaller manual](https://pyinstaller.org/en/stable/).
A Windows container lane or a maintainer-approved native smoke-test procedure
must be defined before E7. The current command policy confines development to
containers; this study does not authorize a host-command exception or add CI.
.NET cross-publishing also needs a native execution check.

An offline trial must start from provisioned assets with network unavailable and
record attempted network activity, not rely on a populated model cache.
The native Windows trial should cover installation without a developer SDK,
Unicode/long paths, selection, cancellation, restart, output persistence,
uninstallation/data retention and source updates/deletion.

## Result record for a future run

For each E-ID, retain the question, approved scope, artifact/config hashes,
machine profile, corpus revision, commands actually run, raw measurements,
aggregates, failures, deviations, limitations and maintainer decision.
Publish a candidate comparison with reasons for inclusion/rejection; do not copy
upstream speed rankings into the result column.

Current result: **no E1-E9 experiment executed**. The present PR validates the
research documents and OpenSpec structure only.
