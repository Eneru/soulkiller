# Versioned fixture result records

The [ninth extraction tranche](../openspec/changes/implement-versioned-fixture-records/proposal.md)
bridges one [in-memory fixture result](bounded-corpus-run.md) and the
[opaque run store](confined-run-storage.md). Saving remains an explicit caller
operation, with strict versioned JSON and typed re-reading.

## Explicit encode, store and read

Launch the existing offline profile (`--network none --memory 3g --cpus 2`)
before invoking the runner. Inside it:

```sh
PYTHONPATH=experiments/text-pdf/src python - <<'PY'
from pathlib import Path
from soulkiller_text import (
    create_run_store, decode_fixture_record, encode_fixture_record,
    open_run_store, run_corpus,
)

workspace = Path.cwd()
corpus = "experiments/text-pdf/corpus"
run = run_corpus(workspace, corpus)
row = run.fixtures[0]
with create_run_store(workspace, corpus, "fixture-record-example-001") as store:
    store.write_record("fixture-001", encode_fixture_record(row))
with open_run_store(workspace, corpus, "fixture-record-example-001") as store:
    restored = decode_fixture_record(store.read_record("fixture-001"), row.specification)
assert restored == row
PY
```

Choose a new run ID before repeating: creation never reuses an existing directory.
This saves one row, not an entire run or a checkpoint. The codec itself neither
reads sources nor writes files. The expected specification must come from an
already accepted corpus; a frozen dataclass alone does not prove acceptance.
On later inspection, the caller must supply the same accepted fixture context.

## Exact version-1 JSON

| Field | Meaning |
| --- | --- |
| `schema_version` | Exact integer `1` |
| `fixture_id`, `format`, `source_sha256` | Expected identity and revision |
| `result` | Matching TXT/PDF result, or `null` for unfinished work |
| `output_bytes` | Observed transport bytes, or `null` when unavailable |
| `unfinished_reason` | Non-complete schedule status, or `null` for returned results |

TXT results contain exactly `outcome` and `text`. Only success has nonempty text;
Unicode, line endings and code-point offsets are preserved.
PDF results contain exactly `outcome`, `pages`, `total_pages` and `missing_pages`.
Pages contain exactly `page_number` and `text`. Physical pages, partitions and
the declared page ceiling use the reviewed worker evidence rules.
Supervisor-only PDF failures have no page evidence and an unavailable total.

Returned results retain known nonnegative observed counts through the existing
worker ceiling plus one overflow-detection byte. Counts are independent of JSON
size. Unfinished rows retain zero for never-started work; only cancellation or
cleanup interruption may retain unavailable output. Unknown never becomes zero.
Reference expectations need not equal observed extraction outcomes.

Both directions validate objects/wire: unknown/missing/duplicate fields,
unsupported versions, boolean numeric values, invalid enums/types, inconsistent
evidence, malformed Unicode/JSON and source-binding mismatches fail.
Child-response protocols remain unchanged: persisted supervisor observations
do not grant a child permission to claim those outcomes.

## Bounds, errors and interpretation

Compact deterministic ASCII JSON escapes without normalization. Its payload
must fit 10 MiB minus the store's 48-byte frame; metadata and escaping count.
Evidence is never truncated. Temporary JSON objects/encoding are not a
process-memory sandbox.

`FixtureRecordError` is a `ValueError` with fixed `category`:
`invalid_fixture_record` or `fixture_record_too_large`. Messages exclude supplied
paths, text and raw diagnostics. Filesystem operations retain their separate
`RunStoreError` semantics. Invalid codec input cannot itself create scratch files.

A valid row represents the current fixed UTF-8/pypdf workers, not a complete
comparison report. Labels, annotations, candidate/environment inventory,
aggregate accounting, measurement methods and run-wide ordering require their
own context. Revision checks and storage digests do not authenticate authorship,
truth, persona memory or provenance.

## Verification and follow-up

```sh
bash tools/checks/check.sh all
```

Independent literal-wire tests cover both directions, forged objects, malformed
wire, all current worker outcomes, exact byte boundaries and real-store reopen.
The existing connected/offline lanes retain real worker regressions. Every
maintained source remains in >=70% executable-line coverage, Ruff, strict mypy,
Bandit and the existing security/advisory gates. Existing Python runtime, editor
configuration and eligible CI apply; no new dependency/image/trigger is needed.

Next: versioned run context and automatic checkpoints connecting rows to the
scheduler, before CLI, scoring, Docling and the reviewed comparison.
This delivery does not save automatically or prove crash/power-loss recovery.
