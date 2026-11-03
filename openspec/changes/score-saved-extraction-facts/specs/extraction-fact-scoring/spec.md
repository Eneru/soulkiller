# Saved extraction fact checks

## ADDED Requirements

### Requirement: Read-only reference checks
The score command SHALL compare saved extracted evidence against independently
authored annotations in the saved manifest, without extracting again, writing
records or reopening current source files. It SHALL retain integrity validation
and clearly disclose the saved run status.

#### Scenario: Inspect an earlier extraction
- **WHEN** the operator runs score --run-id demo-001 after extraction
- **THEN** the report identifies expected quotes, observed outcomes and resolving evidence locations without running a worker

### Requirement: Separate recovery and source location
Reports SHALL distinguish exact quote recovery from correct reference location.
Matching SHALL preserve case, whitespace and Unicode code points without
normalization. TXT locations SHALL use zero-based, end-exclusive offsets;
PDF references SHALL use one-based pages and offsets within saved page text.
The report SHALL show one resolving observed location per recovered annotation.

#### Scenario: Fact moved to another PDF page
- **WHEN** an expected page-2 quote occurs only on saved page 1
- **THEN** recovery counts the quote and location correctness does not, with page 1 shown

#### Scenario: TXT quote occurs at a different offset
- **WHEN** a quote appears outside its annotated TXT range
- **THEN** recovery and exact-location correctness differ and the actual range is shown

### Requirement: Honest denominators and outcomes
All saved annotations SHALL remain in denominators, including failed, partial,
unfinished or missing observations. Expected outcome agreement SHALL be reported
separately. Unannotated documents SHALL be visible and zero annotations SHALL
be shown as 0/0 without a perfect-score claim. Unknown observations SHALL NOT
be counted as expected outcome matches. These checks SHALL NOT claim semantic
quality, reading order, parser ranking or an approved acceptance threshold.

#### Scenario: Extraction failed for an annotated input
- **WHEN** a saved annotated document has no recovered text
- **THEN** its facts remain in the denominator and its observed failure remains visible

#### Scenario: Check an interrupted saved run
- **WHEN** a document row is missing but its reference annotations are saved
- **THEN** those annotations remain expected, their evidence is unavailable and the report labels the run incomplete

### Requirement: Usable text and JSON
The command SHALL provide terminal-safe readable output and exact JSON, using
the existing show exit semantics for complete, incomplete and cancelled runs.
Quality mismatches SHALL be reported without inventing an automatic pass threshold.

#### Scenario: Read an expected invalid-encoding outcome
- **WHEN** a complete run contains the expected invalid-encoding fixture
- **THEN** the outcome agreement is visible and scoring can complete successfully without treating that fixture as recovered text
