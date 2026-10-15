# Confined immutable run storage

## ADDED Requirements

### Requirement: Exclusive output namespace
The store SHALL use only a fresh .soulkiller-local/evaluation/<run-id>/ under the
trusted Soulkiller workspace. It SHALL validate source/output separation in both
directions, including directory identity aliases, before creating output.
It SHALL refuse unsafe names, unsupported enforcement and existing runs without
overwriting or removing user-owned state.

#### Scenario: Existing run or source overlap
- **WHEN** a requested run already exists or overlaps the selected source tree
- **THEN** the operation fails before output writes and existing bytes remain unchanged

#### Scenario: Symlink in a directory boundary
- **WHEN** workspace, output parents or run traversal encounter a symlink
- **THEN** its target is not followed or modified

### Requirement: Descriptor-anchored bounded publication
Record writes SHALL accept only exact bytes and safe leaf names. The store SHALL
enforce encoded-frame per-record/aggregate/count ceilings before scratch creation.
It SHALL handle short writes, request file/directory synchronization and publish
without replacement. Existing records SHALL NOT be overwritten.
No ordinary rename/replace or recursive cleanup SHALL occur.

#### Scenario: Exact budget and an additional record
- **WHEN** a store reaches its encoded-byte or record-count ceiling
- **THEN** the next record is rejected without creating output or altering existing records

#### Scenario: Final name collides
- **WHEN** publication finds a pre-existing file, symlink, FIFO or directory
- **THEN** the existing entry remains untouched and publication is not reported as success

### Requirement: Complete bounded inspection
Read-only reopening SHALL create nothing and permit no record writes.
Known records SHALL be read through bounded no-follow descriptors and accepted
only as stable single-link regular complete frames with matching length/digest.
Opaque bytes SHALL NOT be described as authenticated or typed comparison reports.

#### Scenario: Reopen a complete binary record
- **WHEN** a successfully published record is read after closing/reopening
- **THEN** its exact original payload is returned without enabling mutation

#### Scenario: Malformed or linked record
- **WHEN** a record is truncated, oversized, mutated, linked or has an invalid frame
- **THEN** inspection fails safely without exposing partial accepted data

### Requirement: Preserve interrupted storage state
After a write-phase exception, prior committed records SHALL remain inspectable,
the failing handle SHALL prohibit further writes and transient file descriptors
SHALL close. Its directory descriptor SHALL close on context exit/close. Incomplete scratch SHALL remain distinguishable from committed records.
Failures SHALL NOT clean up user-owned state or claim successful synchronization.

#### Scenario: Cancellation during a later write
- **WHEN** an operator interrupts after an earlier record was committed
- **THEN** the earlier record remains readable and incomplete scratch is not accepted as a record

### Requirement: Scoped quality integration
Every maintained source SHALL enter existing static/security checks and >=70%
executable line coverage. Routine tests SHALL use synthetic data without providers.
The store SHALL NOT claim automatic runner persistence, report serialization,
power-loss recovery or native Windows performance.

#### Scenario: Delivery verification
- **WHEN** the ready PR is prepared
- **THEN** actual connected/offline checks and deferred integration work are documented
