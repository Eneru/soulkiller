# Bounded sequential corpus run

The [seventh extraction tranche](../openspec/changes/implement-bounded-corpus-run/proposal.md)
connects [verified corpus snapshots](pdf-corpus-input.md) to the fixed TXT and
[native PDF workers](pdf-worker-supervision.md). It provides one in-memory pass,
not a completed comparison, persisted report, scoring operation or application.

## Run and inspect

Use the existing image in a container launched with `--network none --memory 3g
--cpus 2`, mounting only Soulkiller. The ordinary connected devcontainer
deliberately refuses a corpus run, including a TXT-only selection.

Inside the offline container, from Soulkiller's root:

```sh
PYTHONPATH=experiments/text-pdf/src python - <<'PY'
from pathlib import Path
from soulkiller_text import RunLimits, run_corpus

run = run_corpus(Path.cwd(), "experiments/text-pdf/corpus", RunLimits())
print(run.status, run.output_bytes)
for row in run.fixtures:
    outcome = row.result.outcome if row.result is not None else row.unfinished_reason
    print(row.specification.fixture_id, outcome, row.output_bytes)
PY
```

The API loads and validates the whole explicit manifest before launching a
worker. It processes immutable snapshots in manifest order without reopening
source paths. It accepts no alternate executable, candidate or unverified list
of snapshots. Corpus validation errors reject the run before any worker starts.

The frozen `CorpusRunResult` contains `status`, `fixtures` and `output_bytes`.
Each frozen `FixtureRun` retains the source specification, its existing
TXT/PDF `result` or `unfinished_reason`, and observed `output_bytes`.
A complete schedule may include invalid encoding, encrypted/malformed PDF,
partial extraction or other worker failures. It does not establish comparison
success, authorship, factual truth or persona memory.

## Guards and accounting

`RunLimits` allows only finite positive wall budgets through 600 seconds,
positive exact integer output budgets through 50 MiB and a validated
`WorkerLimits`. Boolean numeric values and larger ceilings are rejected.
Worker defaults remain 60 seconds, 2 GiB address space and 10 MiB combined output.
The existing manifest ceilings remain 32 fixtures, 5 MiB/source and 20 declared
PDF pages total. These are evaluation guards, not production capacity promises.

Before the first worker, require supported Linux exit observation and the
existing inherited offline-topology check. A worker that subsequently reports
`unsupported_environment` stops later scheduling. Other per-file failures
leave independent fixtures eligible while aggregate budgets remain available.

Each worker receives the smaller of its own wall/output limit and the remaining
run allowance. The monotonic run budget includes elapsed corpus loading.
Synchronous input reads/process creation cannot be preempted by this scheduler;
elapsed time is checked on return. Existing bounded cleanup can extend return
time past the scheduling deadline. This is not a parent-process hard stop.

Output accounting observes bytes actually read from stdout and stderr, including
failed responses and discarded diagnostics. It does not reconstruct encoded
response size from accepted text. The existing cap reads at most one additional
overflow-detection byte; that byte is counted. A detected aggregate overflow can
therefore exceed the allowance by one byte, then stops all later launches.
The count does not measure every byte a child generated, Python object memory
or serialized report size.

A PDF's declared `page_count` is also its worker page ceiling. More actual pages
produce an explicit `page_limit` finding. Declarations remain independent
reference metadata; no source/page discrepancy is silently resolved or scored.

## Unfinished work and exceptions

`RunStatus` names `COMPLETE`, `TIME_LIMIT`, `OUTPUT_LIMIT`,
`UNSUPPORTED_ENVIRONMENT`, `CANCELLED` and `CLEANUP_FAILURE`.
Every accepted fixture has a row, including later work that never started.
Never-started rows have zero observed output. Interrupted current calls have
unknown output (`None`); the total is also unavailable if any observation is
unknown. Completed outcomes and their measured bytes remain inspectable.

After corpus acceptance, cancellation raises `CorpusRunCancelled`, preserving
`KeyboardInterrupt` catch semantics. Unconfirmed cleanup raises
`CorpusRunCleanupError`, preserving `WorkerCleanupError` catch semantics and
taking precedence over cancellation. Both carry a frozen `.result` with the
completed, interrupted and unstarted rows. No later worker launches.
Interruption before corpus acceptance has no accepted snapshot list to report.

These records live in memory. Catching an exception lets the caller inspect
them; process exit/crash does not create durable evidence. Confined output
directories and bounded opaque records are now available through the separate
[run-store foundation](confined-run-storage.md). Typed report records, automatic
interruption checkpoints, scoring, Docling, three-run comparison measurements
and a CLI remain subsequent reviewed work.

## Verification and integrations

```sh
bash tools/checks/check.sh all
```

From a POSIX host terminal opened in Soulkiller, the permitted container launch
for the complete offline Python regression suite is:

```sh
docker run --rm --init --network none --memory 3g --cpus 2 \
  --mount "type=bind,source=${PWD},target=/workspaces/soulkiller,readonly" \
  --workdir /workspaces/soulkiller soulkiller-dev bash tools/checks/python.sh tests
```

Independent synthetic tests cover real mixed extraction, exact observed transport,
failure-then-success ordering, clamped budgets, unfinished rows, early refusal,
cancellation and cleanup. All maintained sources participate in >=70% executable
line coverage, Ruff, strict mypy and full Bandit with the unchanged exact-launch
policy. Existing native Python editor/runtime integration covers this package;
no dependency, image rebuild or extension change is needed.

The existing eligible PR-to-main/SemVer-tag quality job repeats the offline suite
with its already built image after canonical connected checks. No extra trigger,
runner matrix, paid service or benchmark is introduced. CLI/backend results do
not claim manual editor UI, native Windows performance or parser rankings.
