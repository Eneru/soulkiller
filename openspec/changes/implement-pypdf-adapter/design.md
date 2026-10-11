# Design: native pypdf adapter foundation

## Context

The maintainer approved the parent evaluation in PR #13 and confirmed PR #16
was reviewed and merged on 2026-10-11. This is a small adapter/fixture tranche.
The source-machine Windows 8/16 GiB profiles remain evaluation targets, not
results from the Ubuntu container.

## Goals / Non-Goals

Provide an internal, sequential adapter seam for trusted synthetic bytes, with
independently tested page attribution and safe outcomes. Provision the exact
dependency in the devcontainer rather than relying on manual installations.

No user-file ingestion entrypoint, PDF manifest schema, PDF worker/protocol,
full run resource profile, output persistence, scoring or comparison is added.
The adapter alone is not a resource/network enforcement or security boundary.
The existing TXT supervision contract is unchanged. PDF worker integration
must establish the full approved boundary before an ingestion/run API is exposed.

## Decisions

### Dependency and configuration

Use base pypdf 6.20.0, without extras. The approved design recorded 6.19.0 as
a proposed metadata snapshot. The October 9 release adds filter-count and
accumulated stream-decoding guards; document this maintenance update and verify
the exact wheel hash and Python 3.13 install rather than adopting extra assets.
References: [release history](https://pypdf.readthedocs.io/en/latest/meta/CHANGELOG.html)
and [versioned metadata](https://pypi.org/project/pypdf/6.20.0/).

Import the parser lazily inside the adapter, not through the package's public
TXT exports. Disable external JBIG2 helpers with the public configuration
(`jbig2dec_binary=None`, `disable_legacy_handling=True`) before reading.
Suppress the pypdf logger's output locally to avoid leaking parser diagnostics.
These process-local settings suit sequential evaluation workers; they are not
an application-wide concurrent parser service.

Use in-memory bytes, default-equivalent non-strict reading and plain extraction,
without attachments, actions, URL/path inputs, images, layout debug output,
password input, OCR or fallback. Reject `reader.is_encrypted` before page access,
including empty-password protection. Constructor dependency errors are explicit
dependency blockers, not assumed proof of encryption. The parser can attempt an
empty password internally; no supplied password or optional crypto is added.

### Internal adapter records

`extract_native_pdf(source: bytes, max_pages: int = 20)` is a test/internal seam;
do not export it from the package's public ingestion surface. Reject non-exact
bytes, source sizes above 5 MiB, booleans/non-integer page bounds and bounds
outside 1..20 before invoking the parser. Preserve the exact source SHA-256.

Keep `PdfOutcome`, frozen `PdfPage` and frozen `PdfResult` in separate files.
Result fields are outcome, source_sha256, pages, total_pages and missing_pages.
Pages retain unmodified candidate strings and physical one-based page numbers.
An empty/whitespace-only complete document yields no_text; blank/image-only
pages are retained without claiming OCR need or visual/authorial correctness.
Obtaining page count is parsing, not an external limit: future workers must
guard it before importing or reading.

Reject files above the page cap before text extraction. Known covered/missing
pages remain visible on page failures. Continue independent pages: recovered
pages plus failures yield partial. When no page completes, a uniform dependency
or malformed-page failure retains its category; unexpected or mixed failure
kinds yield candidate_failure.
Malformed reader/page-tree input and unavailable dependencies are distinct
safe outcomes; unexpected errors become candidate_failure. MemoryError and
cancellation propagate for a future external supervisor rather than being
mistaken for successful/partial extraction. Return no sensitive diagnostics.
The value models are not a future child-protocol validation boundary.

### Independent fixtures and tests

A minimal deterministic PDF writer generates explicit text operations,
Helvetica/WinAnsi pages, blank/image sentinels and a correct xref. No extra
writing dependency is introduced. Expected facts/page assignments are authored
in reusable test fixtures, never captured from the extractor. Base pypdf may
encrypt an independently written protected sentinel solely in tests.

Include every maintained adapter/model/writer module in existing all-source
line coverage. Use independent Arrange/Act/Assert cases through adapter and
writer behavior, with error/boundary doubles where a tiny synthetic PDF cannot
reliably induce resource/cancellation/page faults. No helper-layout tests.
Keep functions preferably <=50 lines.

### Execution and tool integration

Use the current pinned runtime, native Python/Ruff/mypy editor settings and
pytest discovery, with base pypdf in the image hash lock. Retain Gitleaks,
Hadolint, full Bandit policy, static checks, advisory checks and >=70% executable
line coverage through canonical CLI/hooks/editor/CI entrypoints.

Real fixture tests run in a fresh `--network none --memory 3g --cpus 2` container
with only Soulkiller mounted read-only. These small trusted tests are not proof
of a user-file parser sandbox, a PDF supervisor or Windows performance.
Build and start the changed image; verify imports, writing and persistence.
No CI trigger or automatic timed comparison is added.

## Risks / Trade-offs

- Page-tree/content decompression can allocate heavily: no arbitrary-file API
  is exposed until the separately reviewed PDF worker boundary is integrated.
- Tolerant parsing is not comprehensive PDF validation; no_text has multiple
  causes and plain output may differ from visible ordering.
- AES dependencies may be unavailable: retain an explicit blocker, with no
  automatic extras installation, password collection or fallback.
- Library settings are process-local; future workers configure before parsing
  and verify bounded protocol results independently.

## Migration Plan

Add modules and the pinned dependency alongside existing TXT interfaces, run
the full checks and submit one ready PR. Record PR #16 merge in its task list.
PDF corpus/worker integration follows only after review; parent evaluation
tasks remain incomplete until both candidates/runner/reporting are delivered.
