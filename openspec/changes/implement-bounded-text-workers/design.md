# Design: bounded TXT workers

## Context

See [proposal](proposal.md) and the
[worker contract](specs/bounded-text-workers/spec.md). PR #15 delivered confined
synthetic TXT input and verified immutable byte snapshots. The approved parent
[evaluation design](../evaluate-text-pdf-extraction/design.md) already defines
worker budgets; this tranche tests supervision before adding a PDF dependency.

## Goals / Non-Goals

**Goals:** enforce the existing per-worker guards around the trusted standard
UTF-8 baseline, with observable failure handling and bounded cleanup.

**Non-goals:** arbitrary plugins or commands, PDF parsing, scoring, result
persistence, run-level scheduling, network enforcement, hostile-code containment,
native Windows execution and performance comparisons. The parent contract's
offline container topology and whole-run limits remain future integration work.

## Decisions

### Byte API and immutable records

Expose `run_text_worker(source: bytes, limits: WorkerLimits = defaults)`.
Separate frozen limits and results into individual modules. A result contains
`source_sha256`, `outcome` and `text`; failed/empty results contain no text.
Non-byte source input raises `TypeError`; invalid limits or oversized input raise
safe `ValueError` before spawning. Wall time is positive, finite and at most
60 seconds; integer memory ranges from 64 MiB to 2 GiB and integer output from
1 byte to 10 MiB. Boolean limits are rejected. Lower limits support deterministic
boundary tests without increasing reviewed budgets.
No manifest or source-path parameter is accepted: forwarding the already verified
snapshot avoids a filesystem validation/reopen race.

### Fixed isolated interpreter and early resource guard

Launch the current pinned interpreter in isolated mode with a trusted bootstrap
script and fixed argument structure; do not invoke a shell, use environment-selected
executables or accept user-supplied worker paths. Supply only fixed `LANG` and
`LC_ALL=C.UTF-8` to the child, without parent credentials, Python import settings
or dynamic-loader variables. The bootstrap uses standard
library modules to set and read back Linux `RLIMIT_AS` before importing the TXT
candidate. Bootstrap exit code 3 specifically identifies unavailable enforcement;
exit code 4 specifically identifies a caught `MemoryError`; other unexplained
nonzero exits remain candidate failures. The address-space ceiling
is not an RSS measurement or a Linux/container/Windows performance claim.

Apply the guard in the child bootstrap rather than a parent `preexec_fn`, which
can deadlock in threaded callers. Process isolation avoids making a decoder
cooperative timeout responsible for protecting its own supervisor. The bootstrap
and any shared protocol helpers remain maintained source in coverage.

### One deadline and capped pipe transfer

The parent uses nonblocking pipes and selectors for stdin, stdout and stderr.
One monotonic deadline starts before launch and includes transfer and exit;
a blocking stdin write or an early response must not bypass it. Python cannot
interrupt every operating-system process-creation call: account for elapsed spawn
time immediately after it returns, and document this timing limitation.
Read bounded chunks and compare combined stream bytes against the output budget
before appending. Do not use unbounded `communicate()` accumulation.
Capture standard error only within that cap and never expose it in public errors.

A strict JSON response has exactly integer `version: 1` and the declared
hash/outcome/text fields.
Reject duplicates, non-finite values, extra fields, invalid types and inconsistent
text/outcome values; verify the source hash independently in the parent.
Only complete input delivery and a complete valid response with pipe EOF and
exit zero can become success. If stdin closes before all snapshot bytes are
delivered, retain that failure while waiting for bounded exit observation: exits
3/4 still identify unsupported enforcement or explicit allocation failure; an
otherwise plausible success becomes `candidate_failure`. Timeout/output
overflow override response and exit classifications. A reported `MemoryError`
can be classified as resource exhaustion; a signal or unexplained crash remains
a candidate failure because its cause is unknown.

### Process-group cleanup is part of the result boundary

Launch a fresh session and use Linux `waitid(..., WNOWAIT)` to observe exit
without reaping. Retain the leader PID until group termination to avoid signaling
a reused PID/session; missing `waitid`/`WNOWAIT` support fails before launch.
Kill the owned process group, then perform leader reaping with a 2-second wait
on success, failure and cancellation. Cleanup also runs
when a child fails before sending a response or leaves inherited pipes open.
Only an already absent process group permits suppressing `ProcessLookupError`;
other kill/wait failures raise `WorkerCleanupError` with a safe message and stop
sequence continuation. Never classify a returned fixture outcome as proof of cleanup when
it has not been confirmed. Killing a process group does not contain a child that
creates a different session; the trusted TXT worker is the only supported code.

### Existing toolchain and short review scope

No new package or language is needed. The pinned interpreter, pytest/coverage,
Ruff, strict mypy, Bandit, advisory audit, container-side editor extensions and
canonical checks already apply. Extend meaningful synthetic tests and retain all
new source in the 70% line-coverage gate; record branch coverage separately.
Use actual isolated-process smoke tests in a container launched with networking
disabled, 3 GiB memory and at most 2 CPUs, mounting only Soulkiller. This verifies
the explicit test topology; the API itself does not disable networking.
Do not alter CI triggers or add implicit timed benchmark runs.

The required `subprocess` import and fixed `Popen` call trigger Bandit B404/B603
heuristics. Permit only those findings at the reviewed `supervise.py` import/call
through an exact AST-checked exception policy over the complete JSON scan.
Require exactly those two findings at the approved import/call locations and
validate the call options; extra/duplicate findings, unsafe options or scanner
errors fail. A normal Bandit baseline is unsuitable because its finding equality
ignores source lines, code and counts. Keep every other scanner finding active
and verify the exception policy with independent failure/regression tests. No caller-selected command or shell
execution is allowed. Document this rationale in the check guidance.

## Risks / Trade-offs

- Bootstrap or protocol allocation can fail before a response exists -> report
  bounded candidate/protocol failure; do not infer a precise memory cause.
- Timing tests can be flaky under load -> use short lower budgets with generous
  external test bounds and deterministic blocking synthetic workers.
- A leader can exit while descendants retain pipes -> retain the same deadline,
  kill the launched process group and test inherited-pipe cleanup.
- Limits are guards around trusted code, not a security sandbox -> introduce no
  PDF parsing until this tranche is reviewed; future candidate integration must
  separately enforce the offline topology and whole-run constraints.

## Migration Plan

Add the worker API alongside the existing pure decoder and corpus loader without
changing their public behavior. Verify the tranche, submit one ready PR and wait
for maintainer review/manual merge before the PDF adapter tranche. Rollback is
removing this additive API; it creates no persistent state or schema migration.
