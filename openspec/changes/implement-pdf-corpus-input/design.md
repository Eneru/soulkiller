# Design: confined synthetic PDF corpus inputs

## Context and goals
The maintainer confirmed PR #17 review and merge on 2026-10-11. This fifth
tranche prepares sources for later PDF workers; it does not weaken the parent
execution boundary or adopt an application ingestion interface.

## Decisions
### Preserve TXT compatibility
Keep `parse_manifest(bytes)` strict version 1, returning TXT `CorpusFixture`
records with existing outcomes and exact source-span expectations. Add
`parse_evaluation_manifest(bytes)` accepting versions 1 and 2 and returning a
tuple of TXT/PDF specifications. Version 2 retains the exact root fields and TXT
fixture shape; PDF entries additionally require `page_count`. The generic
`load_corpus` uses that parser; the committed version-1 corpus is unchanged.
Use cohesive shared validation helpers rather than copying the security rules.
Keep one class per file, explicit imports and functions preferably <=50 lines.

### Independent PDF metadata
A frozen `PdfCorpusFixture` retains the existing common metadata, literal
`format="pdf"`, `page_count`, expected outcome and a tuple of frozen
`PdfFactAnnotation(page_number, quote)` records. Expected PDF outcomes are only
`success`, `no_text`, `encrypted_pdf`, `malformed_input`; infrastructure failures
such as missing dependencies/timeouts are findings, not reference expectations.
Only success may have annotations. Facts are nonempty strings without surrogate
code points and physical one-based nonboolean integer page numbers. Page count
is an independently declared positive integer, bounded by the approved initial
20-page corpus budget; every fact page must fit. At most 32 annotations apply
per fixture, as for TXT. Annotation array order preserves supplied order but
does not yet define a reading-order scoring contract. No candidate offsets are
invented for PDF references.

The sum of declared PDF pages in a manifest must stay within the parent initial
corpus budget. This validates annotations and intended work only: declarations
do not establish actual page counts or enforce parser allocation limits.
Malformed/protected sentinels can declare their independently known intended
page count, while actual recovery remains unavailable until supervised parsing.

### Parser-free loading
Retain Linux directory-descriptor confinement, strict exact fields, duplicate
keys/constants/IDs/paths rejection, all existing byte/file bounds and no-partial
tuple behavior. Read each selected source exactly once and hash original bytes.
On TXT inputs, retain strict decode/outcome/span validation. On PDF inputs,
return the exact bytes after revision verification without decoding, invoking
pypdf, checking signatures or treating file extensions as format evidence.
Declared outcomes, page counts and quotes are reference metadata, not extraction
results. Do not import the native adapter/parser through the loader or public
exports. Actual parsing/outcome/page/fact verification must run in a later
bounded worker before a user-file runner is delivered.

### Runtime and quality
No added package, image, editor setting or extension is required. Existing
pypdf remains in the image for adapter tests; the loader itself uses stdlib only.
The image interpreter, native Ruff/Pylance/mypy and pytest discovery already
cover added modules/tests. Preserve all-source executable line coverage >=70%,
full Bandit policy, pinned audits/scans and the canonical hook/CLI/eligible CI.
Use tiny synthetic PDF bytes and independent facts; no personal data or timed
benchmark. Tests exercise schema/limits, confinement/stale sources, deferred
PDF expectations, parser-free loading and version-1 regression behavior.

## Risks and follow-ups
Declared counts can be wrong: future workers independently discover pages under
external resource guards. Frozen records are value containers, not a validation
boundary when constructed directly. Hash matching establishes source revisions,
not truth, identity or extraction correctness. The existing TXT worker protocol
is unchanged; PDF supervision/offline enforcement, scoring and reports follow
in separately reviewed tranches.

## Delivery
Validate the full canonical gates and offline Python suite, strict OpenSpec,
documentation links, Git whitespace and unchanged LICENSE/workflow triggers.
Publish one ready PR with the verified App bot, then await human review/manual
merge. Keep parent comparison tasks incomplete and record the confirmed PR #17
merge in its task list.
