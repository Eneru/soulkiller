# Synthetic TXT corpus inputs

## ADDED Requirements

### Requirement: Explicit bounded manifest
The loader SHALL accept only the versioned synthetic TXT schema, at most 32
fixtures and a 128 KiB manifest. It SHALL reject malformed/duplicate-key/nonfinite
JSON, unknown fields, invalid types, unsupported formats/languages, duplicate
IDs/paths, escaping paths and invalid hashes/annotation spans before fixture reads.

#### Scenario: Independently annotated bilingual corpus
- **WHEN** a valid manifest selects invented French/English TXT fixtures
- **THEN** only the listed inputs are selected and explicit author/subject labels are preserved without inference

#### Scenario: Invalid manifest or source path
- **WHEN** the schema, path, size or uniqueness constraints are violated
- **THEN** the loader raises a named CorpusError before reading fixture content

### Requirement: Confined bounded source snapshots
On Linux the loader SHALL anchor reads to a caller-supplied trusted workspace and
relative corpus root using directory descriptors. It SHALL reject symlink roots,
parents/leaves, nonregular and multiply linked files before reading their content.
Each source SHALL be at most 5 MiB; mutation/hash mismatch SHALL fail. Returned
immutable records SHALL contain exactly the verified bytes and declared metadata.

#### Scenario: Valid verified source
- **WHEN** a listed regular file beneath the selected corpus matches its declared hash
- **THEN** the loader returns its exact bytes without modifying inputs or scanning other paths

#### Scenario: Unsafe or changed source
- **WHEN** a link, special file, escape, missing file, oversized source, mutation or stale revision is encountered
- **THEN** the loader fails with a stable error category and closes acquired descriptors without returning a partial corpus

#### Scenario: Path replaced after acquisition
- **WHEN** a directory entry changes after its original descriptor is acquired
- **THEN** reads remain anchored to acquired descriptors and never reopen that pathname for extraction

### Requirement: Independent resolvable TXT expectations
The loader SHALL reuse strict UTF-8 outcomes and verify declared outcome and exact
zero-based/end-exclusive code-point quotes. Fixture expectations SHALL be authored
independently from extractor outputs; errors SHALL NOT return partially validated
records or turn supplied labels into verified identities.

#### Scenario: Empty, invalid and Unicode text
- **WHEN** synthetic fixtures contain empty/malformed bytes or accented/CRLF/non-BMP text
- **THEN** declared outcomes and exact code-point annotations must match the preserved source snapshot

#### Scenario: Stale expectation
- **WHEN** a declared outcome or annotation disagrees with the verified bytes
- **THEN** the loader raises CorpusError without promoting the source to a valid corpus
