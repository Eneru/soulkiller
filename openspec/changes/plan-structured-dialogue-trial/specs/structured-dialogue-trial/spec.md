## ADDED Requirements

### Requirement: Explicit offline comparison

The dialogue experiment SHALL keep the PR #29 format selectable as a baseline
and provide an explicitly selected structured variant for the same synthetic
inputs and pinned local runtime. Each generating case SHALL send at most one
bounded generation request per format. The comparison SHALL stop after ten
generation requests or 30 minutes, whichever comes first.

#### Scenario: No eligible saved source matches

- **WHEN** either format is selected and the evidence expression has no eligible match
- **THEN** Soulkiller SHALL report uncertainty without starting the model

### Requirement: Application-rendered citations

In the structured variant, the model SHALL provide prose and a separate list
of eligible source IDs. Soulkiller SHALL validate the IDs against the exact
request scope and construct the displayed citation markers and source excerpts.
A sourced answer SHALL cite at least one unique eligible ID and a conflict
SHALL cite at least two. Unknown, duplicate, missing required IDs or
model-authored citation markers in prose SHALL produce a controlled rejection.

#### Scenario: One eligible source supports the answer

- **WHEN** a complete structured response has valid prose and references only the eligible ID S1
- **THEN** Soulkiller SHALL render [S1] and resolve it to the exact saved excerpt and location

#### Scenario: A response cites an unavailable source

- **WHEN** the structured response includes an ID that was absent from the request
- **THEN** the answer SHALL fail citation validation without displaying an accepted reference

### Requirement: Separate quality and mechanical observations

The report SHALL distinguish mechanical citation validity from human assessment
of factual support, language, first-person voice, conflicts, attribution and
resistance to imported instructions. The report SHALL include failures and
unrun cases. The experiment SHALL keep raw retained outputs ignored and
separate from evidence.

#### Scenario: Two citations resolve but the answer invents a second lamp

- **WHEN** a mechanically valid reply treats conflicting descriptions of one lamp as two lamps
- **THEN** the comparison SHALL record a factual-support and conflict-handling failure
