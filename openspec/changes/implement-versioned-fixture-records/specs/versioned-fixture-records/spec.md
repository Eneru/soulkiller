# Versioned fixture result records

## ADDED Requirements

### Requirement: Exact versioned and revision-bound rows
The codec SHALL encode and decode one FixtureRun through exact version-1 JSON.
Decoding SHALL require an accepted caller-supplied fixture specification and
verify fixture ID, format, source revision and applicable page ceiling.
It SHALL NOT reopen sources or treat reference expectations as observed outcomes.

#### Scenario: An independent bilingual TXT row is restored
- **WHEN** a valid record contains accented text and CRLF with the expected identity/revision
- **THEN** decoding preserves exact text and observations and reuses the expected specification

#### Scenario: The record belongs to another source revision
- **WHEN** its ID, format or SHA-256 differs from the supplied specification
- **THEN** decoding fails with a fixed safe error without source I/O

### Requirement: Strict typed observation semantics
Both encoding and decoding SHALL reject malformed typed objects, unknown or
duplicate fields, unsupported versions, invalid numeric types/enums and malformed
Unicode/JSON. Completed observations SHALL retain matching TXT/PDF results and
known counts through the existing one-byte overflow probe. Unfinished rows SHALL
retain a non-COMPLETE reason and zero, or unavailable counts only for interrupted
cancellation/cleanup. PDF coverage and supervisor-only failures SHALL remain
distinct. The child-response protocols SHALL NOT be broadened.

#### Scenario: A supervisor timeout is persisted
- **WHEN** a completed supervised PDF call timed out with unavailable page evidence
- **THEN** the row retains timeout, no invented pages/count and its observed transport bytes

#### Scenario: An interrupted call has unknown output
- **WHEN** a cancelled or cleanup-failed row has no result and unavailable output
- **THEN** JSON null remains unavailable rather than becoming zero

#### Scenario: A forged row claims inconsistent evidence
- **WHEN** text/page evidence, result type, observation count or unfinished reason violates the schema
- **THEN** encoding and decoding refuse that representation without returning accepted evidence

### Requirement: Bounded create-only storage compatibility
Successful encoded payloads SHALL fit the existing record ceiling including the
store's 48-byte frame. The codec SHALL preserve evidence without truncation and
perform no filesystem writes. Callers SHALL use the reviewed RunStore explicitly.

#### Scenario: Escaping expands a payload past its budget
- **WHEN** encoded JSON and the frame exceed 10 MiB
- **THEN** encoding fails rather than truncating text or bypassing storage guards

#### Scenario: A row is stored and reopened
- **WHEN** valid encoded bytes are written through a fresh RunStore and read after reopening
- **THEN** decoding restores the row while existing names remain protected from replacement

### Requirement: Documented maintainable functions
New or changed functions SHALL have meaningful documentation, including private
helpers. Documentation SHALL explain relevant low-level/OS assumptions, resource
ownership and failure behavior when applicable.

#### Scenario: A private helper implements an OS-specific operation
- **WHEN** a new or changed helper depends on platform flags or descriptors
- **THEN** its documentation explains the concept and relevant ownership/cleanup assumptions
