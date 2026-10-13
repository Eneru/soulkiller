# Bounded sequential corpus run

## ADDED Requirements

### Requirement: Atomic ordered synthetic selection
The entry SHALL accept only a workspace/corpus reference and validated run profile.
It SHALL validate and snapshot every selected source before starting a worker,
preserve manifest order and source metadata, and select only the fixed TXT/PDF
workers. Invalid sources or profiles SHALL fail before candidate launch.

#### Scenario: A later source hash is stale
- **WHEN** the selected corpus contains a hash mismatch
- **THEN** no worker starts and the invalid run is rejected

#### Scenario: Invalid text precedes a valid PDF
- **WHEN** the run has remaining guards and offline enforcement
- **THEN** the TXT error remains visible and the PDF receives its own result in manifest order

### Requirement: Early offline enforcement
The runner SHALL verify supported Linux exit observation and inherited offline
topology before the first worker, including TXT-only selection. Unavailable
enforcement SHALL stop scheduling with explicit unfinished rows.
A worker reporting unavailable enforcement SHALL stop further launches.

#### Scenario: Connected TXT-only corpus
- **WHEN** the inherited namespace is connected
- **THEN** no TXT worker starts and every selected row is unfinished with unsupported_environment

### Requirement: Observed aggregate resource guards
Profiles SHALL tighten only the approved 600-second and 50-MiB run ceilings.
The runner SHALL clamp each worker wall/output allowance to the remaining run
budgets and count actual combined stdout/stderr bytes read, including failures
and a maximum one-byte overflow probe. It SHALL NOT reconstruct transport
measurements from accepted text or discard consumed stderr bytes.
No later worker SHALL start once an aggregate guard is exhausted.

#### Scenario: Remaining run time is smaller than the worker limit
- **WHEN** a worker is about to start
- **THEN** its supervisor deadline uses the remaining run time

#### Scenario: A worker exhausts the remaining output budget
- **WHEN** observed output reaches the remaining allowance or its overflow probe
- **THEN** consumed bytes remain visible and any later fixture is unfinished

### Requirement: Complete and unfinished evidence remain distinct
Every accepted selected fixture SHALL have one immutable row containing either
its verified worker result or its explicit unfinished reason. Completed file
failures SHALL NOT be dropped or turned into successful extraction.
COMPLETE SHALL describe only schedule completion, not comparison success.
PDF workers SHALL use each declared page_count as their page ceiling; a larger
actual count SHALL remain an explicit page_limit finding.

#### Scenario: All files finish, with some errors
- **WHEN** every call returns within available guards
- **THEN** the schedule is complete and every failed outcome remains inspectable

#### Scenario: Actual PDF pages exceed the reference declaration
- **WHEN** the guarded parser observes more pages than the fixture declares
- **THEN** its page_limit outcome is retained without hiding the discrepancy

### Requirement: Partial interruption and cleanup records
Cancellation and cleanup failure after corpus acceptance SHALL stop subsequent
launches and preserve immutable completed/unfinished records on exceptions.
The exceptions SHALL preserve KeyboardInterrupt and WorkerCleanupError catch
semantics. Interrupted unknown output counts SHALL be unavailable, never zero.
In-memory records SHALL NOT be presented as durable reports.

#### Scenario: Cancellation follows a completed fixture
- **WHEN** an operator interrupts the next call
- **THEN** the exception carries the completed row and explicit interrupted/unstarted rows

#### Scenario: Worker cleanup cannot be confirmed
- **WHEN** cleanup raises its distinct failure
- **THEN** no later worker launches and the exception carries partial records

### Requirement: Compatible quality integration
Existing worker APIs, protocols and the exact reviewed launch policy SHALL
remain compatible. Every maintained source SHALL enter existing static/security
checks and >=70% executable line coverage. Real mixed-worker cases SHALL execute
in a bounded offline container; Linux correctness SHALL NOT establish Windows
performance, completed comparison scoring or persisted interruption evidence.

#### Scenario: Delivery verification
- **WHEN** the ready PR is prepared
- **THEN** executed connected/offline checks and deferred report/comparison work are documented
