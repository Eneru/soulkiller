# Native PDF adapter foundation

## Purpose

Define the internal native-page seam and independent synthetic fixtures for
the approved extraction evaluation. This tranche exposes no user-file runner
and does not claim to implement the parent offline/supervision boundary.

## ADDED Requirements

### Requirement: Immutable bounded adapter input

The internal adapter SHALL accept only immutable bytes of at most 5 MiB and
an integer page ceiling from 1 through 20. It SHALL reject boolean or invalid
page bounds and invalid source types before parser execution. It SHALL preserve
the source revision hash and SHALL NOT accept paths, URLs or passwords.

#### Scenario: Invalid input precedes parsing
- **WHEN** the source type, byte size or page ceiling is invalid
- **THEN** a safe input error is raised before the parser is invoked

#### Scenario: Actual pages exceed the cap
- **WHEN** a parsed fixture has more pages than the accepted ceiling
- **THEN** page_limit records the known count without extracting page text

### Requirement: Native pages with physical attribution

The adapter SHALL retain each covered page's plain native text unchanged and
identify pages by physical one-based index. It SHALL report success only for a
fully covered document with meaningful native text. It SHALL report no_text
for fully covered empty/whitespace-only text, retaining empty covered pages.
It SHALL NOT run OCR, infer authorship, diagnose a scan or claim visual ordering.

#### Scenario: A bilingual fixture has facts on page two
- **WHEN** its native text is extracted
- **THEN** the independently expected facts resolve to physical page 2

#### Scenario: Blank or image-only pages have no native text
- **WHEN** the adapter completes those pages
- **THEN** no_text preserves the covered page records without invoking OCR

### Requirement: Visible failures and partial coverage

The adapter SHALL distinguish encrypted_pdf, malformed_input,
unsupported_dependency, candidate_failure and partial. It SHALL reject detected
protection even if the empty password would unlock it. Known covered/missing
pages SHALL remain explicit. Partial extraction SHALL NOT become complete
success. MemoryError and cancellation SHALL propagate for external supervision;
errors SHALL NOT expose input text or parser diagnostics.

#### Scenario: Protected or malformed bytes precede a valid fixture
- **WHEN** the fixtures are extracted independently
- **THEN** safe explicit failures precede a valid fixture's own result

#### Scenario: One of two pages fails
- **WHEN** a page fails while another completes
- **THEN** partial retains the completed physical page and identifies the missing page

#### Scenario: A dependency fails before encryption can be inspected
- **WHEN** construction raises a parser dependency error
- **THEN** the result is unsupported_dependency rather than invented encryption evidence

### Requirement: Explicit narrow parser configuration

The adapter SHALL use the pinned base parser without extras and disable
external JBIG2 command helpers before parsing. It SHALL NOT invoke attachment,
action, image-export, layout-debug, network, model or provider operations.
Its internal API SHALL NOT be represented as a resource/network enforcement
boundary; full PDF worker integration remains required before ingestion use.

#### Scenario: Configuration is established before reading
- **WHEN** a trusted fixture is handed to the parser
- **THEN** external image helper execution is disabled before reader construction

### Requirement: Independent maintained fixtures and quality gates

Bilingual expected facts and source pages SHALL be authored independently of
extractor output. The maintained deterministic writer and adapter modules SHALL
be included in all-source executable line coverage with a floor of 70%.
Existing pinned scans, native editor/runtime integration and canonical CI
execution points SHALL accompany the dependency. Tiny real fixture tests SHALL
also execute in a bounded network-disabled container.

#### Scenario: The changed image is rebuilt
- **WHEN** a clean development container starts
- **THEN** the exact base parser imports through the image interpreter and routine tests require no downloads or credentials

#### Scenario: Fixture results are delivered
- **WHEN** the implementation PR is prepared
- **THEN** it records executed checks and preserves the distinction between adapter tests, future worker integration and unmeasured Windows performance
