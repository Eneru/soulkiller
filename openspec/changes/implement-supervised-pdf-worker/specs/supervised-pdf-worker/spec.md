# Supervised native PDF worker

## ADDED Requirements

### Requirement: Fixed bounded PDF byte worker
The API SHALL accept immutable bytes with existing source/resource bounds and
an integer nonboolean page ceiling from 1 through 20. It SHALL reject invalid
inputs before launch and SHALL select only the fixed reviewed interpreter and
native candidate bootstrap. Results SHALL preserve original hashes and
physical page records without paths/passwords or fallback.

#### Scenario: Invalid source or profile
- **WHEN** bytes, resource limits or page bound are invalid
- **THEN** a safe input error occurs before any process launches

#### Scenario: Valid bilingual PDF bytes
- **WHEN** the worker runs under its verified offline guards
- **THEN** the result preserves independently expected facts and physical page attribution

### Requirement: Early external offline and memory guards
The bootstrap SHALL verify its inherited Linux namespace has exactly loopback
and establish/read back RLIMIT_AS before package/candidate/parser imports.
Guard unavailability or connected topology SHALL stop parsing with an explicit
unsupported_environment outcome. The externally supplied Docker network-none
topology SHALL NOT be presented as an API-created or hostile-parser sandbox.

#### Scenario: Ordinary connected devcontainer
- **WHEN** the namespace includes a nonloopback interface
- **THEN** the PDF worker refuses before importing the parser

#### Scenario: Guard setup fails
- **WHEN** memory enforcement or bounded topology inspection is unavailable
- **THEN** no candidate is invoked and unavailable enforcement remains explicit

### Requirement: Shared deadline and mandatory cleanup
PDF workers SHALL reuse the reviewed sanitized non-shell launch, bounded pipes,
combined output cap, deadline, exit observation and owned group cleanup. Timeout
and output overflow SHALL override apparent responses. Cancellation SHALL
propagate only after cleanup; cleanup failure SHALL stop continuation.

#### Scenario: Worker times out or overflows output
- **WHEN** a guard is exceeded despite a response prefix
- **THEN** no page evidence is accepted and the worker group is stopped/reaped

#### Scenario: A worker completes or is cancelled
- **WHEN** control leaves supervision
- **THEN** mandatory pipe closure and owned process-group cleanup are attempted

### Requirement: Independently verified PDF responses
The parent SHALL independently validate strict version-2 JSON, source hash,
field/types/Unicode and ordered unique covered/missing page partitions.
Success/no_text SHALL require complete coverage and appropriate text; partial
SHALL contain both covered and missing pages. Declared supervisor failures SHALL
NOT cross the candidate wire. Over-limit page counts SHALL retain no proportional
missing-page allocation. Invalid responses SHALL yield protocol_error with no
unverified evidence.

#### Scenario: A page is missing
- **WHEN** valid partial coverage is received
- **THEN** covered/missing pages remain explicit without complete success

#### Scenario: Inconsistent or stale response
- **WHEN** hash, count, page partition, types or outcome invariants are invalid
- **THEN** the supervisor discards page evidence and reports protocol_error

### Requirement: Existing quality and compatibility
TXT worker API/protocol SHALL retain their behavior. Every added maintained
source SHALL participate in canonical static/security checks and executable
line coverage with a 70% floor. Real PDF worker success/failure cases SHALL
execute in the bounded network-disabled container without credentials/models;
connected refusal SHALL NOT be represented as successful parser execution.

#### Scenario: Delivery verification
- **WHEN** the PR is prepared
- **THEN** executed connected/offline checks and deferred whole-run/Windows work are reported separately
