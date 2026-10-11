# Synthetic PDF corpus inputs

## ADDED Requirements

### Requirement: Explicit compatible mixed selection
The corpus API SHALL accept a strict version-2 manifest selecting synthetic TXT
and PDF fixtures, retaining exact fields, existing byte/fixture limits, path
confinement and duplicate rejection. Version 1 and its TXT-only parser SHALL
retain their existing behavior. All metadata SHALL be validated before any
selected fixture is read.

#### Scenario: Mixed bilingual selection
- **WHEN** a valid version-2 manifest explicitly selects invented TXT/PDF inputs
- **THEN** only those sources are loaded with unchanged declared labels and language

#### Scenario: Version-1 PDF selection
- **WHEN** PDF metadata is supplied under version 1
- **THEN** validation fails before any fixture content is read

#### Scenario: Invalid later metadata
- **WHEN** a later version-2 entry violates a schema or page-budget rule
- **THEN** earlier valid sources are not read

### Requirement: Independent physical-page facts
PDF metadata SHALL retain an independently declared positive page count and
nonempty quote/physical-page annotations, with at most 32 annotations per
fixture. Page values SHALL be nonboolean integers within the declared count;
declared PDF pages SHALL total at most the approved initial 20-page corpus
budget. PDF reference outcomes SHALL be success, no_text, encrypted_pdf or
malformed_input; only success SHALL contain annotations. No candidate-derived
offsets, identity inference or infrastructure-failure expectations SHALL be
introduced.

#### Scenario: A French reference fact belongs to page two
- **WHEN** its validated reference annotation is loaded
- **THEN** the quote and physical page 2 remain unchanged without claiming recovered evidence

#### Scenario: Invalid page or aggregate budget
- **WHEN** a page/count type, page range or declared aggregate bound is invalid
- **THEN** the manifest fails before fixture reads

### Requirement: Confined parser-free PDF snapshots
The loader SHALL read selected PDF bytes through the existing confined bounded
descriptor boundary and verify their exact source hash before returning a
complete immutable corpus. It SHALL NOT decode PDF as TXT, import/invoke a PDF
parser, validate PDF extraction expectations or reopen a source for extraction.
An unsafe/missing/oversized/changed/stale source SHALL fail without returning a
partial tuple or modifying sources.

#### Scenario: Protected or malformed bytes are selected
- **WHEN** their bytes match the independently declared source hashes
- **THEN** verified snapshots retain the expected metadata without attempting parsing

#### Scenario: A later PDF source is stale
- **WHEN** its bytes differ from the manifest revision
- **THEN** no earlier snapshots are returned as a valid corpus

#### Scenario: Deferred PDF extraction checks
- **WHEN** declared PDF facts or page counts disagree with eventual parser output
- **THEN** loading alone SHALL NOT claim those extraction expectations were verified

### Requirement: Existing quality integration
Added maintained corpus source SHALL participate in canonical static/security
checks and all-source executable line coverage with a 70% floor. Tests SHALL
use synthetic data without credentials/models and cover compatibility,
metadata boundaries, parser-free operation and confined source failures.
Existing native runtime/editor integration and eligible CI triggers SHALL
remain intact.

#### Scenario: Delivery checks run
- **WHEN** the tranche is prepared for review
- **THEN** executed checks and deferred supervised PDF integration are reported separately
