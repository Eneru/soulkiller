# Confined synthetic TXT corpus

The [second extraction tranche](../openspec/changes/implement-confined-text-corpus/proposal.md)
adds input validation before PDF candidates. Python remains an evaluation tool;
this is a Linux devcontainer library, not an application ingestion command or a
native Windows reader. No directory scan, PDF parser, worker, report or benchmark
is implemented here.

## Use the explicit corpus

From Soulkiller's root **inside the devcontainer**, inspect the five hand-authored
synthetic fixtures without a package install, model, network or credentials:

```sh
PYTHONPATH=experiments/text-pdf/src python - <<'PY'
from pathlib import Path
from soulkiller_text import load_corpus

records = load_corpus(Path.cwd(), "experiments/text-pdf/corpus")
for record in records:
    print(record.specification.fixture_id, record.specification.outcome, len(record.source))
PY
```

The caller supplies a trusted absolute workspace anchor and a canonical relative
corpus path. The loader reads that corpus's fixed `manifest.json` and only its
listed sources. A later CLI must supply the Soulkiller workspace anchor itself;
a manifest cannot choose it. Temporary test workspaces are container-internal.
Passing a different trusted anchor is a caller decision, not authenticated access
control. The API returns a tuple of frozen `LoadedFixture(specification, source)`
records. Reuse their exact verified bytes for later extraction; do not reopen their
pathnames. Public model constructors are value containers, not verified inputs.

## Manifest version 1

See the [literal example](../experiments/text-pdf/corpus/manifest.json). The root
contains exactly integer `schema_version: 1` and a nonempty `fixtures` list.
Each fixture contains exactly:

| Field | Meaning / validation |
| --- | --- |
| `id` | Unique 1–64 ASCII alphanumeric/underscore/hyphen characters; alphanumeric first |
| `path` | Unique relative slash path under the corpus; no empty/dot/parent component, absolute root, backslash, colon, NUL or surrogate; cannot select root `manifest.json` |
| `sha256` | Exactly 64 lowercase hexadecimal digits, matching original source bytes |
| `format` / `language` | `txt` only / `fr` or `en`; no encoding or format guessing |
| `author_label` / `subject_label` | Explicit nonempty labels, at most 128 Unicode code points, unchanged; no surrogate or inferred/verified identity |
| `outcome` | `success`, `no_text` or `invalid_encoding`, checked against strict UTF-8 decoding |
| `annotations` | At most 32 exact `start`/`end`/`quote` objects; nonboolean integer, nonempty zero-based/end-exclusive code-point spans and exact source quotes; none for unsuccessful outcomes |

JSON is strictly UTF-8 and rejects duplicate keys, nonfinite constants, malformed
or excessively nested documents, unknown fields and incorrect types. The entire
schema is validated before reading any fixture, including invalid later entries.
The complete corpus fails if any revision, outcome or annotation disagrees: no
partial tuple is returned or silently scored against stale expected data.

The committed sources contain French CRLF/accents/combining/non-BMP characters,
English LF, explicit empty/invalid-byte sentinels and contradictory third-party
statements. Text/outcome/span expectations were authored independently of the
extractor; computed hashes freeze only the source revisions. Labels preserve
attribution without choosing a statement's truth. Scoped [-text attributes](../.gitattributes)
retain exact TXT bytes across Git checkout, including CRLF and malformed UTF-8.
The scoped cr-at-eol whitespace attribute recognizes the intended CRLF terminator;
other trailing-whitespace checks remain active.
There is no maintained corpus generator or PDF-generation dependency in this tranche.

## Read boundary, limits and errors

Limits are **128 KiB per manifest, 32 fixtures and 5 MiB per source**, hence at most
160 MiB of retained raw corpus bytes. These are experiment guards, not Windows
minimums or measured product capacity. Linux directory descriptors anchor each
workspace/corpus/parent component; `O_NOFOLLOW` rejects symlinks at every level.
Leaves are opened read-only/nonblocking and inspected before reading: only regular
files with one link are accepted. Bounded chunks and one overflow byte enforce the
size cap. Device/inode/mode/link count/size/mtime/ctime are compared before/after;
atime is excluded because reads can legitimately update it. Acquired descriptors
are closed on success/error and path replacement cannot redirect them.

`CorpusError.category` gives a stable reason; messages exclude source text/paths:

| Category | Meaning |
| --- | --- |
| `invalid_manifest`, `duplicate_fixture`, `invalid_path` | Invalid schema/value, duplicate selection or noncanonical path |
| `manifest_too_large`, `input_too_large` | Manifest or source exceeds its byte ceiling |
| `unsafe_file`, `source_unavailable` | Link/nonregular input or filesystem open/read failure |
| `source_changed`, `source_mismatch` | Observed metadata/size mutation or stale declared SHA-256 |
| `expectation_mismatch` | Decoded outcome or exact annotation disagrees |
| `unsupported_platform` | Linux descriptor flags/relative-open capability unavailable |

This boundary is not a parser sandbox, physical-storage immutability guarantee or
protection against privileged mount changes. Regular-file I/O can block; the
[TXT worker foundation](text-worker-supervision.md) separately bounds decoder
execution after loading. Loader I/O deadlines and actual PDF page bounds remain
future integration work.
No file is written/deleted by the loader; failed runs leave source content alone.

## Verify and continue

Run `bash tools/checks/python.sh static`, `bash tools/checks/python.sh tests` and
`bash tools/checks/check.sh all`. All new source modules participate in the existing
component's >=70% executable **line** gate; branch coverage is reported separately.
Fixtures/config/tests remain outside its source denominator. Independent tests
exercise schema errors, exact Unicode expectations, filesystem links/special files,
size/mutation/replacement races and descriptor cleanup. Routine tests are offline.

The existing pinned runtime, native Python/Ruff/mypy integrations, pytest discovery,
hook/CLI and eligible CI already cover this src/tests tree; no new environment
package or workflow is needed. [Editor guidance](python-editor.md) explains the
current suite and remaining UI checks. PR #14's editor operation was confirmed by
the maintainer; this tranche's CLI/backend results are reported separately.
The [trusted TXT worker tranche](text-worker-supervision.md) adds process guards
without a PDF parser. Continue with reviewed pypdf/PDF integration, then native
Docling/scoring/reports.
