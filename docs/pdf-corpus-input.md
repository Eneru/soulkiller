# Confined synthetic PDF corpus

The [fifth extraction tranche](../openspec/changes/implement-pdf-corpus-input/proposal.md)
adds explicit PDF selection alongside TXT after PR #17's adapter was reviewed
and merged. This Linux devcontainer library loads source snapshots; it does not
parse a PDF, run an evaluation, infer identity or establish extraction results.

## Manifest versions and records

The existing [version-1 corpus](../experiments/text-pdf/corpus/manifest.json) and
`parse_manifest(bytes)` remain TXT-only. The new
`soulkiller_text.evaluation_manifest.parse_evaluation_manifest(bytes)` accepts
versions 1 and 2. Version 2 permits mixed TXT/PDF selection, retaining the
existing exact root fields, TXT entry shape and strict JSON/path/hash rules.

PDF entries retain `id`, `path`, `sha256`, `format`, `language`,
`author_label`, `subject_label`, `outcome` and `annotations`, and add
`page_count`:

| Field | PDF reference meaning |
| --- | --- |
| `format` / `language` | Explicit `pdf` / `fr` or `en`; extension/content guessing is absent |
| `page_count` | Independently declared positive nonboolean integer; declared PDF pages sum to at most 20 in the initial corpus |
| `outcome` | Expected `success`, `no_text`, `encrypted_pdf` or `malformed_input` |
| `annotations` | At most 32 exact `page_number`/`quote` objects; only for success |
| `page_number` | Physical one-based nonboolean integer within the declared count |
| `quote` | Independently authored nonempty string without surrogate code points |

Annotation order is retained but no reading-order score is defined here.
Reference facts have no candidate-derived offsets. Infrastructure failures such
as missing dependencies, timeouts or resource exhaustion remain execution
findings rather than expected corpus content.

`PdfCorpusFixture` and `PdfFactAnnotation` are frozen value models, separate from
TXT metadata/span records. `LoadedFixture.specification` can hold either source
type. These constructors do not independently validate forged records.

## Loading and deferred checks

`load_corpus(workspace_root, corpus_path)` accepts either manifest version.
It validates the complete schema before any source read, then uses the existing
[descriptor-bound input boundary](text-corpus-input.md#read-boundary-limits-and-errors)
to load only selected files, at most 5 MiB each, and verify original-byte hashes.
A stale/unsafe/missing/oversized source prevents a complete tuple from being
returned. Sources are never written, deleted or reopened for extraction.

TXT outcome and exact code-point quote checks are unchanged. PDF loading checks
only source revision and reference metadata: it does not decode as TXT, import
pypdf, inspect a page tree, verify a signature or check an extraction outcome.
Malformed/protected fixtures remain eligible snapshots when their declared
hash matches. Misleading extensions do not change explicit format selection.

Declared page counts and quotes are **unverified extraction expectations**.
The [supervised PDF worker](pdf-worker-supervision.md) independently validates
actual page coverage, outcomes and response text. Matching recovered fact
locations against these expectations remains whole-run evaluation work.
A declaration cannot bound parser
allocation or replace the external execution boundary. The
[internal adapter](native-pdf-adapter.md) remains a separate trusted-fixture seam;
no arbitrary-file runner is exposed.

## Validation and runtime

Run from Soulkiller's root inside the devcontainer:

```sh
bash tools/checks/python.sh static
bash tools/checks/python.sh tests
bash tools/checks/check.sh all
```

Tests use independently supplied metadata and tiny synthetic inputs, including
mixed languages, page/type/schema bounds, stale hashes, links/special files,
snapshot preservation and parser-free loading. The existing version-1
regression suite remains active. Every maintained source module participates
in the existing >=70% executable line-coverage gate; no exclusion is added.

No dependency or image/editor setting is added. The image interpreter, native
Ruff/Pylance/mypy diagnostics and pytest discovery already cover this source
tree; see [editor setup](python-editor.md) and
[CLI/hooks/eligible CI checks](quality-checks.md#experimental-python-checks).
CLI results do not claim manual editor UI or native Windows execution.

The separate [bounded corpus run](bounded-corpus-run.md) now connects these
snapshots and supervised TXT/PDF workers in manifest order. Next: confined
durable reports, independent scoring and Docling. No benchmark, production
stack choice, provider, model or personal-data run is delivered here.
