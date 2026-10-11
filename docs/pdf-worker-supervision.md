# Supervised native PDF bytes

The [sixth extraction tranche](../openspec/changes/implement-supervised-pdf-worker/proposal.md)
connects immutable bytes to the [native pypdf adapter](native-pdf-adapter.md).
It reuses [TXT supervision](text-worker-supervision.md) and independently checks
PDF responses. This is an experimental library seam, without a corpus runner,
report persistence, Docling comparison, benchmark or production-stack choice.

## API and results

`soulkiller_text.run_pdf_worker(source, limits=None, max_pages=20)` accepts exact
immutable bytes only, capped at 5 MiB. Use an already verified
[corpus snapshot](pdf-corpus-input.md); the worker takes no path, password or
alternate command. Invalid bytes or limits fail before launching. The page
ceiling must be an integer from 1 to 20; boolean values are rejected.

`WorkerLimits` retains the reviewed defaults: 60 seconds for launch, transfer,
guard setup, parsing and exit; 2 GiB virtual address space; 10 MiB combined stdout
and stderr. Lower overrides use the [existing ranges](text-worker-supervision.md#limits-and-safe-errors).
Address space is not resident memory or a Windows hardware requirement.

The frozen `PdfWorkerResult` contains a `PdfWorkerOutcome`, original
`source_sha256`, covered `PdfPage` records, `total_pages` and `missing_pages`.
Pages are physical, one-based and preserve exact candidate text. These value
constructors do not authenticate evidence; the public worker validates the
received result before returning it.

| Result | Meaning |
| --- | --- |
| `success` | Complete coverage with at least one meaningful text page |
| `no_text` | Complete empty/whitespace coverage, including a valid zero-page PDF |
| `partial` | Some covered and some missing pages; never complete success |
| `encrypted_pdf` | Detected protection, no supplied password or page evidence |
| `malformed_input` / `unsupported_dependency` / `candidate_failure` | Safe parser/dependency/unexplained failure; known all-page failures retain missing-page attribution |
| `page_limit` | Actual count exceeds the requested ceiling; covered/missing tuples remain empty |
| `timeout` / `resource_limit` / `output_limit` | Observed deadline, explicit allocation failure or combined output cap |
| `protocol_error` | Response rejected independently; no unverified pages returned |
| `unsupported_environment` | Required supervision, memory or offline guard unavailable |

Parser diagnostics are not returned. Supervisor failures contain no page
evidence. Mandatory session termination, pipe closure and reaping run on all
paths; cancellation propagates afterwards and cleanup failure raises
`WorkerCleanupError` rather than silently continuing.

## Execution boundary

The fixed child uses the image interpreter with `-I -B`, a reviewed bootstrap,
a sanitized locale-only environment and no shell. Before package/candidate/pypdf
imports, it establishes and reads back `RLIMIT_AS` and boundedly inspects Linux
`/proc/self/net/dev`. Only an exactly loopback-only namespace is accepted;
connected, unreadable, malformed or unknown topology refuses extraction.

Supply this boundary by launching the trusted image with Docker
`--network none`. The API does not create a network namespace or make an
ordinary devcontainer offline. Loopback remains available. The assumptions are
the reviewed non-root image, stable namespace, no added privileges, only
Soulkiller mounted and no socket or external service. This is not a general
hostile-parser sandbox or protection against a privileged operator changing
interfaces. See [Docker's none driver](https://docs.docker.com/engine/network/drivers/none/)
and [kernel network tables](https://docs.kernel.org/filesystems/proc.html#networking-info-in-proc-net).

## Independent protocol checks

The candidate emits version-2 JSON with exactly `version`, `outcome`,
`source_sha256`, `pages`, `total_pages` and `missing_pages`.
Each page has exactly `page_number` and `text`. The parent rejects duplicate
keys, invalid JSON/UTF-8/constants/depth, extra fields, boolean/inconsistent
counts, surrogate text and stale hashes.

Covered/missing numbers must be ordered, unique, disjoint and partition a
bounded known count. Success, no_text, partial and failures each have their own
coverage/text invariants. Over-limit counts carry no proportional allocation.
Only native adapter outcomes cross this wire; supervisor guard failures come
from observation or reserved exits. Timeout/output overflow override even an
apparently valid response. TXT's version-1 protocol remains unchanged.

## Checks and offline execution

Run the connected development checks from Soulkiller's root:

```sh
bash tools/checks/python.sh static
bash tools/checks/python.sh tests
bash tools/checks/check.sh all
```

The connected lane verifies fail-closed refusal, strict protocol and lifecycle
fault handling. After building `soulkiller-dev`, run the complete Python suite
from a POSIX host terminal opened in Soulkiller with this sole Docker launch:

```sh
docker run --rm --init --network none --memory 3g --cpus 2 \
  --mount "type=bind,source=${PWD},target=/workspaces/soulkiller,readonly" \
  --workdir /workspaces/soulkiller soulkiller-dev \
  bash tools/checks/python.sh tests
```

Tests run inside the container with synthetic bilingual/empty/protected/malformed
PDFs and independently expected physical pages. Offline cases assert actual
extraction rather than substituting refusal or skipping them. There are no
credentials, model downloads, paid calls or host development commands.
Advisory audits remain separate explicit network checks.

All maintained source participates in the existing **70% executable line-coverage**
gate, with branches reported separately and no source exclusions. The single
fixed Popen operation retains the narrowly checked Bandit exception; overload
declarations do not permit another launch. Existing native Python
[editor integration](python-editor.md), [CLI/hooks/CI gates](quality-checks.md#experimental-python-checks)
and pinned dependencies already cover these modules; this source-only tranche
does not require an image rebuild or a new workflow.

Executed results belong in the delivery PR. No timing, household-PC capacity,
native Windows validation or complete parser comparison follows from these
correctness checks. Whole-run ordering, aggregate budgets, expected-fact matching
and bounded reports remain follow-ups.
