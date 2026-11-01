## ADDED Requirements

### Requirement: Run the example with one command
The command SHALL process only the selected validated synthetic corpus in the
approved offline container and save results under a fresh ignored run directory.
It SHALL refuse an existing run without replacement.

#### Scenario: I try the example
- **WHEN** I run the documented example command offline
- **THEN** I see each document's outcome and extracted text or PDF page references and a saved run location

#### Scenario: I repeat the same run name
- **WHEN** I reuse the name
- **THEN** the command fails clearly and my previous results stay unchanged

#### Scenario: I forgot the offline environment
- **WHEN** I launch run in a connected container
- **THEN** it explains the required offline launch and creates no result directory

### Requirement: Read saved results later
The show command SHALL display saved text/pages/errors without rerunning
extraction, in readable text or exact-evidence JSON. Corrupt evidence SHALL fail
inspection. Plain display SHALL escape terminal controls.

#### Scenario: I close and relaunch the container
- **WHEN** I show the same run with the same Soulkiller mount
- **THEN** I can read its saved results without the original source files

### Requirement: Preserve progress
Each returned row SHALL be saved before another worker starts. On a caught
cancellation the tool SHALL retain completed rows and mark unfinished work.
Unconfirmed persistence SHALL never be reported as success.

#### Scenario: I interrupt a run
- **WHEN** cancellation is caught after a document has completed
- **THEN** the previous result remains readable and later work is explicitly unfinished

#### Scenario: The process stops without a final status
- **WHEN** a run has saved metadata but no summary
- **THEN** inspection labels it incomplete and missing rows unavailable without inventing successful results
