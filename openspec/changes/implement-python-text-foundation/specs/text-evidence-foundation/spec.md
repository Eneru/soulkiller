# Text evidence foundation

## ADDED Requirements

### Requirement: Exact in-memory UTF-8 extraction
The evaluation helper SHALL accept source bytes without filesystem or network
access, compute their SHA-256, strictly decode UTF-8 and preserve every code point.
It SHALL return immutable success, no_text or invalid_encoding outcomes.

#### Scenario: Bilingual text and original line endings
- **WHEN** valid French/English bytes contain accents, CRLF or LF, BOM, NUL, combining characters or non-BMP characters
- **THEN** the helper returns success with exact unchanged text and the original byte hash

#### Scenario: Empty input
- **WHEN** the bytes are empty
- **THEN** the helper returns no_text and the empty source hash

#### Scenario: Invalid UTF-8
- **WHEN** decoding would require replacement characters or a guessed encoding
- **THEN** it returns invalid_encoding with no decoded text and retains the original hash

### Requirement: Resolvable code-point evidence
Evidence SHALL contain the original source hash, a zero-based inclusive start,
an exclusive end and the exact original text slice. It SHALL reject non-integer
(including boolean), empty, negative, reversed or out-of-range spans and
non-success extraction outcomes.

#### Scenario: Accented and non-BMP quote
- **WHEN** a valid span selects text containing multi-byte UTF-8 characters
- **THEN** offsets count Unicode code points and the quote equals that source slice

#### Scenario: Invalid reference
- **WHEN** an invalid span or non-success outcome is supplied
- **THEN** the helper raises a documented error without generating evidence

### Requirement: Python quality from its first executable seam
The development environment SHALL provide pinned isolated CPython and hash-locked
quality dependencies, independent tests, all-source executable line coverage
>=70%, lint/format/type/Bandit gates and dependency-advisory checks. Tool errors
and findings SHALL fail. Tests and static analysis SHALL need no credentials or
network; audit network access SHALL use public package metadata only.

#### Scenario: Invalid implementation or dependency
- **WHEN** a selected check finds an error, insufficient line coverage or a known vulnerability, or cannot complete
- **THEN** its canonical command exits unsuccessfully

#### Scenario: Existing execution points
- **WHEN** developers use container commands, the configured local hook/editor tasks or eligible CI
- **THEN** they reuse the image tools and the PR-to-main/SemVer-tag event policy

### Requirement: Native container-side Python editor support
The devcontainer SHALL install versioned VS Code Python, Ruff and mypy integrations
and required Python companion extensions on the container side. Native diagnostics
and pytest discovery SHALL use the image interpreter/tools and the experiment
configuration. Pylance SHALL provide source navigation without a competing type
policy. Full security and coverage gates SHALL remain available through canonical
tasks/CLI/CI; Test Explorer SHALL NOT be presented as enforcing the coverage floor.

#### Scenario: Reopen the experiment in the devcontainer
- **WHEN** the developer rebuilds/reopens with a compatible VS Code and selects the configured image interpreter
- **THEN** Ruff and strict mypy diagnostics are available natively and pytest discovers the synthetic experiment tests without host Python or tool installation

#### Scenario: Existing editor state or tool mismatch
- **WHEN** a prior interpreter selection overrides the configured default or the editor integration cannot use the image tools
- **THEN** the documentation explains how to select the intended interpreter and inspect tool output without claiming that an unexecuted UI check passed
