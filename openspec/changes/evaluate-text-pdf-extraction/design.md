# Design: native extraction evaluation

**Status:** proposed implementation design; this delivery is plan/specs only.
The maintainer confirmed an 8 GiB RAM, CPU-only Windows reference and a 16 GiB
comparison on 2026-10-04. CPU model, Windows version/architecture, storage and
performance expectations remain open. These profiles are not measured minima.

## Context and boundaries

See [proposal](proposal.md), [contract](specs/text-pdf-extraction-evaluation/spec.md)
and [existing E1-E9 evaluation plan](../../../docs/research/soulkiller-evaluation-plan.md).
Start with the independently testable extraction seam. Access, persona style,
memory, retrieval and UI rules do not need to be implemented to compare parsers.
Python is proposed for this experiment only; a production language remains open.
No source-machine SDK/container requirement is adopted for the eventual product.

The initial application access choice is one local manager and unauthenticated
interlocutor labels. Labels identify attributed dialogue, not authenticated
people or permission boundaries. They do not imply remote access, accounts or
unrestricted source/history visibility; detailed application operations remain
outside this extraction contract. The experiment uses invented identities only.

## Proposed candidates and provisioning

Metadata/source snapshot checked 2026-10-04; none installed or compatibility-tested:

| Candidate | Proposed pin / role | Declared direct code terms |
| --- | --- | --- |
| Python | 3.13.16, isolated experimental runtime | PSF license; exact distributed artifact/notices to inventory |
| Standard UTF-8 reader | Same runtime, TXT correctness baseline | Runtime terms |
| pypdf | 6.19.0; default extraction, explicit page iteration | BSD-3-Clause |
| Docling native | docling-slim[convert-core,format-pdf-docling] 2.133.0; docling-parse 7.22.1 | MIT for these packages; transitive/native inventory still required |

Use exact resolved versions, artifact hashes and a reviewed dependency/license
inventory in the implementation. Metadata compatibility is not install evidence.
Pin test/security/lint/type/audit tools at implementation time after checking
maintenance and advisories. Provision only in the devcontainer, with no host
configuration, extra bind mount or Docker socket. Build downloads are separate
from the offline experiment. Do not add a resolver's unexpected model extras
merely to make an import succeed; record/review the blocker.

pypdf documents native extraction, layout limitations and possible large memory
use. Docling's native pipeline emits parser-order text cells without learned
layout, OCR or table recognition. It therefore tests native text/provenance,
not the original E1 learned-layout benefit. Propose explicit native format
selection, both page/picture image generation disabled and parser_threads=1.
Disabling OCR/tables on Docling's standard pipeline is not a model-free path.
Full docling selects the standard bundle, so use the narrow slim candidate.

Primary evidence: [pypdf extraction](https://pypdf.readthedocs.io/en/6.19.0/user/extract-text.html),
[pypdf metadata](https://pypi.org/project/pypdf/6.19.0/),
[Python 3.13.16](https://www.python.org/downloads/release/python-31316/),
[Docling Slim metadata](https://pypi.org/project/docling-slim/2.133.0/),
[parser metadata](https://pypi.org/project/docling-parse/7.22.1/),
[tagged extras](https://github.com/docling-project/docling/blob/v2.133.0/pyproject.toml),
[native pipeline](https://github.com/docling-project/docling/blob/v2.133.0/docling/pipeline/native_pdf_pipeline.py),
[image/thread options](https://github.com/docling-project/docling/blob/v2.133.0/docling/datamodel/pipeline_options.py),
[standard pipeline](https://github.com/docling-project/docling/blob/v2.133.0/docling/pipeline/standard_pdf_pipeline.py),
and [documented native configuration](https://docling-project.github.io/docling/usage/advanced_options/#extract-the-native-content-of-a-pdf).

## Proposed corpus and scoring

Construct a small reviewed corpus, starting below 20 PDF pages in total. Freeze
source bytes/hashes, invented author/subject labels and independent annotations
before candidate runs; do not derive expected text from an extractor. A fixture
writer is maintained executable code and belongs in tests/coverage. Prefer a
minimal reviewed generator; any PDF-writing dependency needs its own pin/notices.

| Existing fixture family | Initial tranche | Independent expected observations |
| --- | --- | --- |
| T01 | French/English UTF-8, accents, LF/CRLF, empty and malformed bytes | Exact decoded text/offsets or explicit encoding/empty outcome |
| P01 | Two-page selectable-text PDF in each language | Known facts on known one-based pages |
| P02 | Two columns and a small table | Fact recovery and ordering labels; no promised table semantics |
| P03 | Blank and image-only sentinel pages | No native text; no OCR or automatic scan diagnosis |
| P04 | Protected, malformed and over-budget fixtures | Named failure; valid subsequent fixture still processed |
| S01 / K01 | Attributed third-party text and contradictory dated statements | Preserve both sources without inferring authorship or choosing truth |
| Boundary variants | Unicode filename, duplicate IDs, stale hashes and escaping paths | Valid Unicode input; invalid manifest rejected before processing |

Score both PDF candidates against the same fact/page annotations. Record exact
fact coverage, correct source-page count, resolvable evidence slices and ordering
violations separately. Define scoring normalization as Unicode NFC plus collapsed
whitespace; keep candidate text unchanged. Count missing facts/failed fixtures in
the report, not just successful ones. These observations do not measure semantic
retrieval, conversation quality or general PDF support. A correct citation slice
proves where candidate text is stored, not that extraction matches visual glyphs.

Propose outputs only in a new .soulkiller-local/evaluation/<run-id>/ directory,
with confined descriptor-based input reads and run/scratch writes; reject parent
or leaf symlinks, path escapes, existing runs and input/output collisions. Preserve
partial outcomes with covered/missing-page metadata, never promoting partial text
to complete success. Do not remove or overwrite user-owned files on failure.

## Proposed run bounds and measurements

The following experiment guards are proposals for this review, not confirmed
product limits or performance promises:

| Guard | Proposed small initial run |
| --- | --- |
| Input | At most 32 fixtures, 20 total PDF pages, 5 MiB per file |
| Work | One candidate/worker at a time; native parser one thread |
| Worker | 60 seconds wall time; 2 GiB virtual address-space ceiling |
| Container | 3 GiB memory ceiling, at most 2 CPU cores, network disabled |
| Output | 10 MiB per fixture, 50 MiB total; 10 minutes total wall time |
| Repetitions | Three fresh-worker runs per candidate; raw records retained |

A 3 GiB container cap is not an 8 GiB Windows profile. Record actual WSL/Docker
and OS resources, separately from the confirmed reference-machine target.
Memory ceilings must identify their metric: address space differs from RSS.
Use an external supervisor, fixed non-shell argument lists, per-worker limits
before importing/parsing, bounded output and termination of the worker group.
Network-off Docker launch needs only the Soulkiller mount, never nested Docker.
Process limits are resource guards, not a claim that a PDF parser is a security
sandbox. Containment and cancellation failures must be tested explicitly.

Measure startup and extraction wall time separately with a monotonic clock;
collect peak worker memory with the process scope/method disclosed. Retain each
run's raw values, report median and range for three observations, and do not
infer meaningful p95 from this tiny sample. Repeated fresh-worker runs are not
machine-cold runs: OS page caches may remain warm. A reusable-parser warm trial
requires a separate declared condition. Include dependency/environment footprint
and errors. No speed/memory ranking or quality threshold is asserted in advance.

Proposed finite-suite harness gates: exact TXT offset resolution; correct page
references for supported simple PDF facts; explicit expected error categories;
no hidden fallback/network/models; bounded failure leaves valid inputs unchanged.
A candidate's missing facts/ordering errors are evaluation findings, not reasons
to hide a row or weaken the harness tests. Larger 1,000-page and Windows trials
need approved profiles/lanes later; do not trigger them automatically in CI.

## Implementation organization and DevSecOps

Propose an isolated experiments/text-pdf package with separate manifest/evidence
models, TXT/PDF adapters, worker supervision, scoring and report modules. Keep
one class per file, explicit collaborators and shared synthetic fixtures. A CLI
would expose manifest validation, bounded run and report operations; these are
proposed interfaces, not runnable commands in this PR.

From the first implementation, add pinned pytest/coverage, Bandit, lint/type
analysis and dependency-advisory checks alongside existing Gitleaks/Hadolint.
Fail on Bandit findings, selected lint/type findings, known dependency findings
or tool execution errors; any narrow exception needs a documented review.
Measure executable line coverage over all maintained experiment source,
including adapters, supervisor, CLI, scoring/reporting and fixture writers;
exclude only tests, generated fixture bytes, third-party code and configuration.
Keep the existing JavaScript/Bash gates independent so they cannot conceal low
Python coverage. Test a failing coverage/scanner case as well as nominal runs.

Document execution points: canonical container CLI; repository-local hooks that
preserve existing hooks; container-side editor feedback; the existing unprivileged
PR-to-main/SemVer-tag lane. Extend its canonical checks at implementation, without
adding main/branch pushes, manual dispatch or a broad runner matrix. PR checks
use small deterministic fixtures and boundary doubles; real candidate smoke
checks use the provisioned offline native dependencies. Timed comparisons remain
explicit local experiments; deeper tag work requires a separately reviewed budget.
ZAP is not applicable to a CLI with no runnable web surface.

## Risks and review checkpoints

- Native dependency imports may still require unexpected extras: prove clean-cache
  installation/import and offline conversion before claiming a usable challenger.
- Empty native text has several causes: report unavailable text, not automatic
  OCR need or success. pypdf does not validate a pre-existing OCR layer's accuracy.
- Native parsing may misorder columns/tables: publish the finding; learned-layout
  Docling would require a separate asset/dependency/resource decision.
- Worker limits/cleanup and output paths can fail: independently exercise timeout,
  resource exhaustion, symlinks, replacement, cancellation and protected inputs.
- No accounts does not authenticate a speaker: preserve attributed labels without
  presenting them as verified identities or an access-control implementation.
- Linux timing is not native Windows proof: E7 needs a reviewed execution lane;
  this plan authorizes no host-command exception or Windows workflow.

After plan review, implement on a fresh branch with provisioned pinned tools,
reviewed hashes/notices and the same checks. Record actual compatibility and
measurements, then request review of candidate findings before stack selection.
No harness, installation, benchmark, application, model or paid call occurs in
this planning delivery. Extraction approval will not authorize retrieval,
remote inference, persona-memory implementation or production adoption.
