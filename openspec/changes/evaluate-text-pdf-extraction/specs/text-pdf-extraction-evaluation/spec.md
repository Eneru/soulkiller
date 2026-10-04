# Text and PDF extraction evaluation

## Purpose

Provide a reproducible, bounded comparison of native text/PDF extraction on
invented French/English documents while preserving inspectable source locations.
These are proposed experimental-tool requirements, pending maintainer review
and implementation; they do not claim application behavior or measured results.

## ADDED Requirements

### Requirement: Explicit synthetic corpus selection

The evaluation tool SHALL process only regular fixture files explicitly listed
in a validated manifest within the selected Soulkiller synthetic corpus root.
It SHALL reject paths outside that root, symlinks, duplicate fixture identifiers,
missing files and source-hash mismatches before starting a candidate. It SHALL
NOT scan personal directories or infer a persona's identity from a filename.

#### Scenario: Manifest selects a bilingual corpus
- **WHEN** a valid manifest lists synthetic French/English TXT/PDF fixtures
- **THEN** only those files are processed and their recorded source hashes match the inputs

#### Scenario: An input escapes the fixture root
- **WHEN** a manifest references an outside path or a symlink
- **THEN** validation fails before candidate processing without reading that target

#### Scenario: Source bytes changed after annotation
- **WHEN** a fixture's bytes do not match the annotated manifest hash
- **THEN** the run is rejected instead of scoring the changed document against stale expectations

### Requirement: Source preservation and resolvable evidence

The tool SHALL preserve input bytes and source metadata supplied by the manifest.
Every extracted passage SHALL identify the fixture, source revision hash,
candidate/configuration and location. TXT locations SHALL use zero-based,
end-exclusive Unicode code-point offsets in strictly decoded UTF-8 source text,
preserving line endings. PDF locations SHALL identify a one-based source page
and zero-based, end-exclusive code-point offsets in that candidate's persisted
page text. PDF text offsets SHALL NOT be reported as raw-file byte offsets or
exact visual coordinates. Extracted text SHALL NOT establish authorship, truth
or persona memory; those meanings remain outside this tool.

#### Scenario: A French fact has accented characters and CRLF endings
- **WHEN** a passage is extracted from a valid UTF-8 TXT fixture
- **THEN** slicing the decoded source at its reported offsets reproduces the passage including the declared line-ending handling

#### Scenario: A PDF has evidence on its second page
- **WHEN** a passage is recovered from source page 2
- **THEN** its page reference and persisted candidate-page text slice resolve to the reported passage without claiming visual-coordinate precision

### Requirement: Visible per-file outcomes

The tool SHALL report an outcome for every scheduled fixture, distinguishing
successful nonempty text, no recoverable native text, unsupported input,
invalid encoding, encrypted PDF, malformed input, timeout, resource limit and
candidate failure and partial extraction. Partial outcomes SHALL disclose
covered/missing source pages where known and SHALL NOT count as complete success
merely because some text exists. It SHALL NOT silently apply OCR, guess TXT encoding, obtain
passwords, switch candidates or discard failed fixtures from the report.
Independent fixtures SHALL remain eligible after one file fails.

#### Scenario: A PDF has no extractable native text
- **WHEN** extraction returns no meaningful text from a blank or image-only PDF
- **THEN** the outcome identifies unavailable native text without claiming that the PDF is necessarily a scan or invoking OCR

#### Scenario: Invalid text and an encrypted PDF precede a valid file
- **WHEN** these fixtures are evaluated without an encoding override or password
- **THEN** the first two have explicit errors and the valid fixture still receives its own outcome

#### Scenario: A candidate recovers only one of two PDF pages
- **WHEN** a candidate returns valid text for page 1 but cannot recover page 2
- **THEN** the outcome is partial, preserves page 1 evidence and identifies the missing page without claiming full success

### Requirement: Confined output and scratch state

Reports and scratch state SHALL be written only inside a dedicated new run
directory under Soulkiller's ignored evaluation-output root, disjoint from the
fixture tree and local credential folders. The tool SHALL reject escaping or
symlink output paths, existing run directories and source-file collisions before
processing. It SHALL NOT overwrite existing files or clean up user-owned state.
An interrupted run SHALL leave its bounded outcomes available for inspection.

#### Scenario: Output points to an existing source or escaping path
- **WHEN** the requested output would overwrite a fixture, reuse an existing run directory or follow a symlink outside the evaluation root
- **THEN** the run fails before writes or candidate processing, preserving existing bytes

### Requirement: Enforced execution boundary

Before processing, the tool SHALL require a validated resource profile defining
file bytes, pages, concurrency, worker wall time, memory and output limits.
Candidates SHALL run sequentially in bounded workers with networking unavailable
and no model/provider configuration or model downloads. Limits SHALL be enforced
outside candidate parsing, and unavailable enforcement SHALL stop the run rather
than claim containment. Timeouts, cancellation and worker failure SHALL retain
inspectable completed outcomes and mark unfinished work without reporting a
complete comparison. Existing input files SHALL remain unchanged.

#### Scenario: Parsing exceeds a worker limit
- **WHEN** an isolated worker exceeds its configured time or memory budget
- **THEN** it is stopped, a bounded failure outcome is recorded, and no successful extraction is invented

#### Scenario: A candidate needs an unavailable dependency or network access
- **WHEN** the approved offline environment cannot execute that candidate
- **THEN** the run records the blocker without downloading assets or falling back to a model-based pipeline

#### Scenario: A run is cancelled after one fixture completes
- **WHEN** the operator cancels the run
- **THEN** the completed outcome remains inspectable and the remaining fixtures are marked unfinished

### Requirement: Independent quality annotations

The reference corpus SHALL contain independently authored fact/page labels and
reading-order expectations, versioned separately from candidate output.
Scoring SHALL record its normalization rules, numerator, denominator and failed
or unsupported cases. Text normalization SHALL NOT alter stored original or
candidate evidence. It SHALL distinguish exact fact recovery, correct page
attribution and reading-order errors, without claiming semantic retrieval,
answer quality or general format coverage from extraction scores.

#### Scenario: Two candidates differ on a two-column PDF
- **WHEN** both outputs are scored against the same independent annotations
- **THEN** fact recovery, source-page correctness and ordering differences are reported separately

#### Scenario: A candidate produces no text for one required fact
- **WHEN** scoring includes that fixture
- **THEN** the missing fact remains visible in the denominator and failure record

### Requirement: Reproducible and qualified result records

Every result SHALL identify the corpus/configuration and artifact hashes, tool
versions, OS/architecture, CPU/RAM, concurrency, conditions, repetitions,
commands actually run and deviations. Reports SHALL retain raw per-fixture
measurements and use declared aggregation rules. They SHALL separate startup
from extraction time and disclose the memory measurement's process scope.
Unavailable metrics SHALL be marked unavailable, never zero or passing.
Linux/container evidence SHALL NOT be described as native Windows evidence or
proof that an 8 GiB household PC meets production requirements. No unexecuted
comparison or unapproved numeric performance threshold SHALL be reported as met.

#### Scenario: Only the Ubuntu devcontainer run exists
- **WHEN** the report is generated without a native Windows run
- **THEN** Linux results are labeled as such and Windows performance/packaging remain unverified

#### Scenario: A worker fails before a metric is collected
- **WHEN** extraction does not finish or the metric is unavailable
- **THEN** the outcome and missing measurement are retained rather than converted into a successful zero-cost result

### Requirement: Security and testing from first implementation

The implementation SHALL provide credential-free unit, integration and CLI
failure tests, pinned Python static/security/dependency checks and at least 70%
line coverage across all maintained executable harness code. Generated fixtures,
third-party code and tests SHALL have explicit justified coverage exclusions.
Scanner/tool failures SHALL fail their gates. Canonical container commands SHALL
also run in CI only for PRs targeting main or valid SemVer version tags; hooks
and container-side editor feedback SHALL have documented execution points.
Performance runs SHALL remain explicit or in a separately reviewed bounded
version-tag lane, with no networked or paid experiment triggered implicitly.

#### Scenario: The maintained Python harness is first delivered
- **WHEN** its implementation PR is prepared
- **THEN** tests, the enforced coverage floor, applicable scans and documented container/CI entrypoints accompany it

#### Scenario: Coverage or a scanner fails
- **WHEN** executable line coverage is below 70% or a required check cannot execute
- **THEN** the quality gate fails instead of accepting a skipped or fabricated result
