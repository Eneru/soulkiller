# Bounded TXT worker foundation

## Purpose

Provide bounded, inspectable outcomes when the experimental extraction tool
runs its trusted UTF-8 baseline against supplied synthetic source bytes.

## ADDED Requirements

### Requirement: Bounded immutable inputs and limits

The worker API SHALL accept only immutable source bytes of at most 5 MiB and
validated execution limits. Defaults SHALL be 60 seconds wall time, 2 GiB virtual
address space and 10 MiB combined standard output and error. Wall time SHALL be
finite, positive and at most 60 seconds; memory SHALL be an integer from 64 MiB
to 2 GiB; output SHALL be an integer from 1 byte to 10 MiB. Booleans SHALL NOT
be accepted as numeric limits. Non-byte source input SHALL raise TypeError;
invalid values or oversized input SHALL raise safe ValueError before worker
launch. The API SHALL NOT reopen a source pathname.

#### Scenario: A validated corpus supplies source bytes
- **WHEN** the confined corpus loader supplies a verified byte snapshot
- **THEN** the worker consumes that snapshot and retains its SHA-256 without reading the fixture again

#### Scenario: An input or limit is invalid
- **WHEN** input exceeds 5 MiB or a limit is invalid or above its ceiling
- **THEN** validation fails before worker launch without exposing source content

### Requirement: Guards precede trusted decoding

The API SHALL use one fixed non-shell worker command, with no caller-selected
command, code or executable. Before importing the TXT candidate, the worker
SHALL establish and verify its Linux virtual address-space ceiling. One external
wall-clock deadline SHALL cover input transfer, output collection and worker
completion. Unavailable enforcement SHALL produce `unsupported_environment`
without candidate processing. The TXT worker SHALL make no network calls or
model downloads; these process guards SHALL NOT be described as a hostile-parser
sandbox or network isolation.

#### Scenario: Input transfer or decoding stalls
- **WHEN** the worker cannot finish within the configured wall-clock limit
- **THEN** the API stops it and returns `timeout` without partial text

#### Scenario: Memory enforcement is unavailable
- **WHEN** the runtime cannot establish or verify the required address-space limit
- **THEN** the API returns `unsupported_environment` instead of unbounded decoding

### Requirement: Verified bounded outcomes

The API SHALL return an immutable result containing the original source hash,
an outcome and text only for successful, nonempty strict UTF-8 decoding.
Outcomes SHALL distinguish `success`, `no_text`, `invalid_encoding`, `timeout`,
`resource_limit`, `output_limit`, `candidate_failure`, `protocol_error` and
`unsupported_environment`. Only an explicit worker-reported memory-allocation
failure SHALL establish `resource_limit`; abnormal termination alone SHALL NOT
be assigned that cause.

The supervisor SHALL enforce the combined output cap before accumulating
excess bytes. It SHALL require a complete, exactly shaped bounded response
matching the original source hash, complete input delivery, end-of-file and a
successful worker exit before accepting decoded text. Early input closure SHALL
NOT count as complete delivery; a plausible response SHALL remain a candidate
failure unless a reserved bootstrap exit identifies its explicit enforcement or
allocation failure. Timeout and output overflow SHALL take precedence. Duplicate keys, non-finite values, unknown fields,
invalid result types and hash mismatches SHALL be rejected. Failures SHALL NOT
promote partial text or disclose standard error, source content or traceback.

#### Scenario: Strict decoding preserves bilingual text
- **WHEN** a worker successfully decodes French or English UTF-8 with CRLF and Unicode characters
- **THEN** its verified result preserves the exact decoded text and original byte hash

#### Scenario: A worker floods either output stream
- **WHEN** combined standard output and error exceed the configured byte cap
- **THEN** the API returns `output_limit` after cleanup without retaining or exposing excess output

#### Scenario: A worker closes input before consuming its full snapshot
- **WHEN** the child closes stdin before all source bytes are delivered and then exits zero with a plausible response
- **THEN** the API returns `candidate_failure` without accepting decoded text

#### Scenario: A plausible response is incomplete or inconsistent
- **WHEN** a response has a wrong hash, invalid schema, extra data or a failing worker exit
- **THEN** no successful extraction is accepted and the applicable protocol or candidate failure remains visible

### Requirement: Cleanup and cancellation are mandatory

Every launched worker SHALL have its process group stopped and its leader reaped
with a maximum 2-second leader-reap wait before a result is returned. Operator cancellation
SHALL propagate only after cleanup. A cleanup failure SHALL raise a safe distinct
error and prevent the caller from continuing a sequence as though termination
were confirmed. The boundary SHALL NOT claim containment of a child deliberately
escaping its process group.

#### Scenario: Cancellation interrupts a blocked worker
- **WHEN** cancellation occurs while a launched worker is active
- **THEN** the worker group is stopped and its leader reaped before cancellation propagates

#### Scenario: Cleanup cannot be confirmed
- **WHEN** terminating or reaping a worker fails
- **THEN** a distinct safe cleanup error is raised instead of returning an ordinary fixture outcome

### Requirement: Foundation checks accompany implementation

The tranche SHALL provide independent synthetic unit and process integration
tests covering nominal decoding, boundary rejection, failed enforcement, timeout,
output limits, invalid protocol, cancellation and cleanup. All maintained worker
source SHALL remain in the existing executable line-coverage metric with its
70% minimum and applicable static/security checks. Validation SHALL run in the
devcontainer, including an actual network-disabled smoke test. Documentation
SHALL identify completed behavior and deferred PDF, runner and containment work.

#### Scenario: The worker tranche is submitted for review
- **WHEN** the implementation is delivered
- **THEN** its tests, measured coverage and actual container checks are reported without claiming PDF or Windows evaluation results
