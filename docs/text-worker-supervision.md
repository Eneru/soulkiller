# Bounded TXT worker supervision

The [third extraction tranche](../openspec/changes/implement-bounded-text-workers/proposal.md)
runs the existing trusted UTF-8 baseline in a supervised child process. It builds
on [confined corpus snapshots](text-corpus-input.md); it does not add PDF parsing,
a comparison runner, reports or performance results.

## API and input

From Soulkiller's root **inside the devcontainer**:

```sh
PYTHONPATH=experiments/text-pdf/src python - <<'PY'
from pathlib import Path
from soulkiller_text import WorkerLimits, load_corpus, run_text_worker

records = load_corpus(Path.cwd(), "experiments/text-pdf/corpus")
limits = WorkerLimits()
for record in records:
    result = run_text_worker(record.source, limits)
    print(record.specification.fixture_id, result.outcome, result.source_sha256)
PY
```

`run_text_worker(source: bytes, limits: WorkerLimits | None = None)` accepts
immutable bytes, not a pathname or command. Reuse the loader's verified snapshot
without reopening its source. Each call starts a fresh worker; the example waits
for one result before starting the next. No source file is changed.

The frozen `WorkerResult` contains `outcome`, `source_sha256` and `text`.
Successful text preserves strict UTF-8 decoding exactly, including accents,
combining characters, BOM, NUL and LF/CRLF. Empty input yields `no_text`; invalid
UTF-8 yields `invalid_encoding`. Failed/empty results contain `text=None`.
Results are value records, not authorship, authenticity or persona-memory proof.

## Limits and safe errors

`WorkerLimits` validates its fields at construction. Overrides can lower the
reviewed defaults within these ranges; boolean numeric values are rejected.

| Guard | Default / accepted range |
| --- | --- |
| Source bytes | At most 5 MiB; fixed input ceiling |
| `wall_seconds` | 60 seconds; finite and greater than 0, at most 60 |
| `address_space_bytes` | 2 GiB; integer from 64 MiB to 2 GiB |
| `output_bytes` | 10 MiB; integer from 1 byte to 10 MiB, stdout and stderr combined |
| Leader cleanup wait | At most 2 seconds, after group termination |

Address space is virtual memory, not RSS. These are experiment guards, not
Windows hardware requirements or a measured memory footprint. The output ceiling
counts encoded response bytes, including JSON escaping and any stderr. A valid
5 MiB source can therefore exceed the default output ceiling.

Non-byte input raises `TypeError("invalid_worker_source")`; oversized bytes raise
`ValueError("worker_input_too_large")`. Invalid limits raise a safe `ValueError`
before spawning. `WorkerCleanupError("worker_cleanup_failed")` means termination
or reaping could not be confirmed: stop a calling sequence rather than continue
as though that worker had completed. Cancellation propagates after cleanup; a
cleanup failure takes precedence. Public failures expose no source text, stderr
or child traceback.

| Outcome | Meaning |
| --- | --- |
| `success` | Complete verified response with nonempty decoded text |
| `no_text`, `invalid_encoding` | Empty input or strict UTF-8 failure |
| `timeout` | Transfer, output collection or worker completion exceeded the deadline |
| `output_limit` | Combined stdout/stderr exceeded the byte cap |
| `resource_limit` | Explicit child-reported memory-allocation failure |
| `unsupported_environment` | Non-Linux caller, missing non-reaping exit observation, or unavailable verified address-space enforcement |
| `candidate_failure` | Launch/I/O error or unexplained nonzero worker exit |
| `protocol_error` | Successful exit but invalid, incomplete or inconsistent response |

A crash or signal alone does not establish memory exhaustion. The trusted
bootstrap reserves exit 3 for unavailable enforcement and exit 4 for a caught
`MemoryError`; ordinary nonzero exits remain candidate failures.

## Execution and protocol boundary

The public API selects the current pinned interpreter, isolated mode and a fixed
trusted bootstrap. It accepts no executable, shell fragment, worker script or
plugin. Its child environment contains only fixed `LANG`/`LC_ALL=C.UTF-8`;
parent secrets, `PYTHONPATH` and dynamic-loader variables are not inherited.
The internal `run_command` helper is a trusted synthetic-test seam, not an
application command-execution interface.

The bootstrap establishes and reads back Linux `RLIMIT_AS` before importing the
TXT candidate. A parent monotonic deadline begins before launch and covers
nonblocking stdin/stdout/stderr transfer and worker completion. Operating-system
process creation is not always interruptible; elapsed spawn time is checked once
that call returns. Excess output is detected before accumulation; stderr counts
toward the cap but is discarded.

The worker emits one versioned JSON object containing exactly `version: 1`,
`outcome`, `source_sha256` and `text`. Validation rejects duplicate keys,
non-finite values, unknown fields, invalid types and hash/text inconsistencies.
Only complete delivery of the input snapshot, a complete valid response, pipe
EOF and exit zero allow text to be accepted. Early stdin closure before all
input is delivered remains `candidate_failure`, even with a plausible hash and
response; reserved bootstrap exits 3/4 still identify their explicit failures.
Timeout or output overflow takes precedence over those exit classifications.
A partial response or later failing exit cannot become success.

Every launched worker starts its own session. Linux `waitid(..., WNOWAIT)`
observes exit without reaping, retaining the leader PID until group termination
so cleanup cannot signal a reused leader PID. Missing support fails before
launch. On success, error or cancellation, the parent kills that process group,
closes its pipes and then reaps its leader with a bounded wait. Only an already absent group permits ignoring
`ProcessLookupError`; other cleanup failures remain distinct. A child deliberately
creating another session can escape group termination: these guards around
trusted code are **not a hostile-parser sandbox**.

The worker makes no network calls or model downloads, but the API does not
disable networking. The complete evaluation's offline topology, run-level limits
and persisted interruption records remain future work.

## Checks and an offline launch

Run inside the devcontainer:

```sh
bash tools/checks/python.sh static
bash tools/checks/python.sh tests
bash tools/checks/check.sh all
```

The existing pinned runtime, Ruff/mypy editor integrations and pytest discovery
cover this component; no new runtime, package, extension or workflow is required.
The [quality entrypoints](quality-checks.md) retain the local hook, container
CLI/tasks and PR-to-main/valid-SemVer-tag CI policy. Routine tests need no
credentials or network; the explicit advisory audit queries public metadata.

All maintained worker modules, including the bootstrap, remain in the component's
**70% executable line-coverage** gate; branches are reported separately. Independent
synthetic cases cover decoding, transfer/output bounds, invalid responses,
unavailable enforcement, cancellation and cleanup. The fixed `subprocess` import
and `Popen` call produce Bandit B404/B603 heuristics. The repository policy
accepts only those two exact findings after checking their `supervise.py` AST
locations and approved call options; the public command is fixed and
`shell=False`. Extra or duplicate findings, unsafe options and scanner errors
fail. A conventional Bandit baseline matches too broadly, so none is used;
there is no global rule skip or inline `nosec` escape.

To exercise the real worker suite with networking unavailable, run this **container
launch** from a POSIX host terminal opened in Soulkiller after building the image:

```sh
docker run --rm --init --network none --memory 3g --cpus 2 \
  --mount "type=bind,source=${PWD},target=/workspaces/soulkiller,readonly" \
  --workdir /workspaces/soulkiller soulkiller-dev bash tools/checks/python.sh tests
```

Only Soulkiller is mounted. Tests use container-internal temporary directories;
the source mount is read-only. This checks the explicit container topology,
not API-enforced network isolation or native Windows performance. Actual results
and coverage belong in the delivery PR; no parser ranking or benchmark follows
from these correctness tests.
